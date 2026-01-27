<?php
session_start();
header('Content-Type: application/json');

$host = 'localhost';
$dbname = 'your_database';
$username = 'your_username';
$password = 'your_password';

try {
  $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);
  $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
  echo json_encode(['success' => false, 'error' => 'Database connection failed: ' . $e->getMessage()]);
  exit;
}

$action = isset($_GET['action']) ? $_GET['action'] : '';

switch ($action) {
  case 'login':
    try {
      $username = $_POST['username'] ?? '';
      $password = $_POST['password'] ?? '';
      $stmt = $pdo->prepare("SELECT id, password FROM users WHERE username = ?");
      $stmt->execute([$username]);
      $user = $stmt->fetch(PDO::FETCH_ASSOC);
      if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['id'];
        echo json_encode(['success' => true, 'message' => 'Login successful']);
      } else {
        echo json_encode(['success' => false, 'error' => 'Invalid credentials']);
      }
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'request_password_reset':
    try {
      $email = $_POST['email'] ?? '';
      $stmt = $pdo->prepare("SELECT id FROM users WHERE email = ?");
      $stmt->execute([$email]);
      if (!$stmt->fetch()) {
        echo json_encode(['success' => false, 'error' => 'Email not found']);
        exit;
      }

      $token = bin2hex(random_bytes(32));
      $hashed_token = password_hash($token, PASSWORD_DEFAULT);
      $stmt = $pdo->prepare("
        INSERT INTO password_resets (email, token, created_at)
        VALUES (?, ?, NOW())
        ON DUPLICATE KEY UPDATE token = ?, created_at = NOW()
      ");
      $stmt->execute([$email, $hashed_token, $hashed_token]);

      $reset_link = "https://innovai.co.uk/reset-password?token=$token&email=" . urlencode($email);
      $subject = "PNJ Password Reset";
      $message = "Click here to reset your password: $reset_link\nThis link expires in 1 hour.";
      $headers = "From: no-reply@innovai.co.uk";
      if (mail($email, $subject, $message, $headers)) {
        echo json_encode(['success' => true, 'message' => 'Reset link sent to your email']);
      } else {
        echo json_encode(['success' => false, 'error' => 'Failed to send email']);
      }
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'verify_reset_token':
    try {
      $email = $_GET['email'] ?? '';
      $token = $_GET['token'] ?? '';
      $stmt = $pdo->prepare("
        SELECT token, created_at FROM password_resets
        WHERE email = ? AND created_at > NOW() - INTERVAL 1 HOUR
      ");
      $stmt->execute([$email]);
      $reset = $stmt->fetch(PDO::FETCH_ASSOC);
      if ($reset && password_verify($token, $reset['token'])) {
        echo json_encode(['success' => true, 'message' => 'Token valid']);
      } else {
        echo json_encode(['success' => false, 'error' => 'Invalid or expired token']);
      }
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'reset_password':
    try {
      $email = $_POST['email'] ?? '';
      $token = $_POST['token'] ?? '';
      $new_password = $_POST['password'] ?? '';

      $stmt = $pdo->prepare("
        SELECT token FROM password_resets
        WHERE email = ? AND created_at > NOW() - INTERVAL 1 HOUR
      ");
      $stmt->execute([$email]);
      $reset = $stmt->fetch(PDO::FETCH_ASSOC);
      if (!$reset || !password_verify($token, $reset['token'])) {
        echo json_encode(['success' => false, 'error' => 'Invalid or expired token']);
        exit;
      }

      $hashed_password = password_hash($new_password, PASSWORD_DEFAULT);
      $stmt = $pdo->prepare("UPDATE users SET password = ? WHERE email = ?");
      $stmt->execute([$hashed_password, $email]);

      $stmt = $pdo->prepare("DELETE FROM password_resets WHERE email = ?");
      $stmt->execute([$email]);

      echo json_encode(['success' => true, 'message' => 'Password reset successful']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'allocate_job':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $submission_id = $_POST['submission_id'] ?? '';
      $job_number = $_POST['job_number'] ?? '';
      $date = $_POST['date'] ?? '';
      $time = $_POST['time'] ?? '';
      $priority = $_POST['priority'] ?? '';
      $client_name = $_POST['client_name'] ?? '';
      $company = $_POST['company'] ?? '';
      $address = $_POST['address'] ?? '';
      $engineer_contact_name = $_POST['engineer_contact_name'] ?? '';
      $engineer_email = $_POST['engineer_email'] ?? '';
      $engineer_phone = $_POST['engineer_phone'] ?? '';
      $site_contact_name = $_POST['site_contact_name'] ?? '';
      $site_contact_email = $_POST['site_contact_email'] ?? '';
      $site_contact_phone = $_POST['site_contact_phone'] ?? '';
      $notes = $_POST['notes'] ?? '';
      $from_schedule = $_POST['from_schedule'] ?? '0';

      $photo_paths = [];
      if (!empty($_FILES['photos']['name'][0])) {
        $upload_dir = WP_CONTENT_DIR . '/uploads/pnj_jobs/';
        if (!file_exists($upload_dir)) {
          mkdir($upload_dir, 0755, true);
        }
        foreach ($_FILES['photos']['name'] as $key => $name) {
          if ($_FILES['photos']['error'][$key] === UPLOAD_ERR_OK) {
            $ext = pathinfo($name, PATHINFO_EXTENSION);
            $filename = uniqid() . '.' . $ext;
            $destination = $upload_dir . $filename;
            if (move_uploaded_file($_FILES['photos']['tmp_name'][$key], $destination)) {
              $photo_paths[] = '/wp-content/uploads/pnj_jobs/' . $filename;
            }
          }
        }
      }
      $photos = implode(',', $photo_paths);

      $stmt = $pdo->prepare("
        INSERT INTO jobs (
          submission_id, job_number, date, time, priority, client_name, company, address,
          engineer_contact_name, engineer_email, engineer_phone,
          site_contact_name, site_contact_email, site_contact_phone, notes, photos
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ");
      $stmt->execute([
        $submission_id, $job_number, $date, $time, $priority, $client_name, $company, $address,
        $engineer_contact_name, $engineer_email, $engineer_phone,
        $site_contact_name, $site_contact_email, $site_contact_phone, $notes, $photos
      ]);

      if ($from_schedule === '0') {
        $stmt = $pdo->prepare("
          INSERT INTO job_schedule (job_number, client_name, brand, date, time, status, notes)
          VALUES (?, ?, ?, ?, ?, 'Scheduled', ?)
        ");
        $stmt->execute([$job_number, $client_name, '', $date, $time, $notes]);
      } else {
        $stmt = $pdo->prepare("UPDATE job_schedule SET status = 'In Progress' WHERE job_number = ?");
        $stmt->execute([$job_number]);
      }

      echo json_encode(['success' => true, 'message' => 'Job allocated successfully']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'get_clients':
    try {
      $stmt = $pdo->query("SELECT client_name, company, address FROM clients ORDER BY client_name");
      $clients = $stmt->fetchAll(PDO::FETCH_ASSOC);
      echo json_encode(['success' => true, 'data' => $clients]);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'get_engineers':
    try {
      $stmt = $pdo->query("SELECT contact_name, email, phone FROM engineers ORDER BY contact_name");
      $engineers = $stmt->fetchAll(PDO::FETCH_ASSOC);
      echo json_encode(['success' => true, 'data' => $engineers]);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'get_site_contacts':
    try {
      $stmt = $pdo->query("SELECT contact_name, email, phone FROM site_contacts ORDER BY contact_name");
      $site_contacts = $stmt->fetchAll(PDO::FETCH_ASSOC);
      echo json_encode(['success' => true, 'data' => $site_contacts]);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'get_job_schedule':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $unallocated = isset($_GET['unallocated']) && $_GET['unallocated'] === '1';
      $query = $unallocated
        ? "SELECT js.* FROM job_schedule js LEFT JOIN jobs j ON js.job_number = j.job_number WHERE j.job_number IS NULL AND js.status = 'Scheduled'"
        : "SELECT * FROM job_schedule ORDER BY date, time";
      $stmt = $pdo->query($query);
      $schedules = $stmt->fetchAll(PDO::FETCH_ASSOC);
      echo json_encode(['success' => true, 'data' => $schedules]);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'add_job_schedule':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $job_number = $_POST['job_number'] ?? '';
      $client_name = $_POST['client_name'] ?? '';
      $brand = $_POST['brand'] ?? '';
      $date = $_POST['date'] ?? '';
      $time = $_POST['time'] ?? '';
      $notes = $_POST['notes'] ?? '';

      $stmt = $pdo->prepare("
        INSERT INTO job_schedule (job_number, client_name, brand, date, time, status, notes)
        VALUES (?, ?, ?, ?, ?, 'Scheduled', ?)
      ");
      $stmt->execute([$job_number, $client_name, $brand, $date, $time, $notes]);
      echo json_encode(['success' => true, 'message' => 'Job schedule added']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'update_job_schedule':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $id = $_POST['id'] ?? '';
      $job_number = $_POST['job_number'] ?? '';
      $client_name = $_POST['client_name'] ?? '';
      $brand = $_POST['brand'] ?? '';
      $date = $_POST['date'] ?? '';
      $time = $_POST['time'] ?? '';
      $status = $_POST['status'] ?? '';
      $notes = $_POST['notes'] ?? '';

      $stmt = $pdo->prepare("
        UPDATE job_schedule SET job_number = ?, client_name = ?, brand = ?, date = ?, time = ?, status = ?, notes = ?
        WHERE id = ?
      ");
      $stmt->execute([$job_number, $client_name, $brand, $date, $time, $status, $notes, $id]);
      echo json_encode(['success' => true, 'message' => 'Job schedule updated']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'delete_job_schedule':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $id = $_POST['id'] ?? '';
      $stmt = $pdo->prepare("DELETE FROM job_schedule WHERE id = ?
      $stmt->execute(['']);
      echo json_encode(['success' => true, 'message' => 'Job schedule deleted']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'get_engineer_diary':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $engineer = $_GET['engineer'] ?? '';
      $date = $_GET['date'] ?? '';
      $query = "SELECT * FROM engineer_diary WHERE 1=1";
      $params = [];
      if ($engineer) {
        $query .= " AND engineer_name = ?";
        $params[] = $engineer;
      }
      if ($date) {
        $query .= " AND date = ?";
        $params[] = $date;
      }
      $query .= " ORDER BY date";
      $stmt = $pdo->prepare($query);
      $stmt->execute($params]);
      $diary = $stmt->fetchAll(PDO::FETCH_ASSOC);
      echo json_encode(['success' => true, 'data' => $diary]);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'add_engineer_diary':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $engineer_name = $_POST['engineer_name'] ?? '';
      $date = $_POST['date'] ?? '';
      $status = $_POST['status'] ?? '';
      $notes = $_POST['notes'] ?? '';

      $stmt = $pdo->prepare("
        INSERT INTO engineer_diary (engineer_name, date, status, notes)
        VALUES (?, ?, ?, ?)
      ");
      $stmt->execute([$engineer_name, $date, $status, $notes]);
      echo json_encode(['success' => true, 'message' => 'Diary entry added']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'update_engineer_diary':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $id = $_POST['id'] ?? '';
      $engineer_name = $_POST['engineer_name'] ?? '';
      $date = $_POST['date'] ?? '';
      $status = $_POST['status'] ?? '';
      $notes = $_POST['notes'] ?? '';

      $stmt = $pdo->prepare("
        UPDATE engineer_diary SET engineer_name = ?, date = ?, status = ?, notes = ?
        WHERE id = ?
      ");
      $stmt->execute([$engineer_name, $date, $status, $notes]);
      echo json_encode(['success' => true, 'message' => 'Diary entry updated']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'delete_engineer_diary':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $id = $_POST['id'] ?? '';
      $stmt = $pdo->prepare("DELETE FROM engineer_diary WHERE id = ?");
      $stmt->execute([$id]);
      echo json_encode(['success' => true, 'message' => 'Diary entry deleted']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  case 'send_whatsapp_message':
    try {
      if (!isset($_SESSION['user_id'])) {
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit;
      }
      $phone = $_POST['phone'] ?? '';
      $message = $_POST['message'] ?? '';
      // Placeholder for WhatsApp Business API integration
      // Requires API key and configuration
      echo json_encode(['success' => true, 'message' => 'Message sent (placeholder)']);
    } catch (Exception $e) {
      echo json_encode(['success' => false, 'error' => $e->getMessage()]);
    }
    break;

  default:
    echo json_encode(['success' => false, 'error' => 'Invalid action']);
}
?>
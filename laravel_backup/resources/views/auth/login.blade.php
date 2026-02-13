<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Login - PNJ Cleaning</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@3.1.0/dist/full.css" rel="stylesheet" type="text/css" />
    <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-slate-50 min-h-screen flex items-center justify-center">
    <div class="card w-96 bg-white shadow-xl border border-slate-100">
        <div class="card-body">
            <h2 class="card-title text-center block mb-4 text-slate-700">PNJ Cleaning Portal</h2>

            <form action="{{ route('login') }}" method="POST" class="space-y-4">
                @csrf
                <div class="form-control">
                    <label class="label"><span class="label-text">Email</span></label>
                    <input type="email" name="email" placeholder="admin@pnjcleaning.co.uk"
                        class="input input-bordered w-full" required />
                </div>
                <div class="form-control">
                    <label class="label"><span class="label-text">Password</span></label>
                    <input type="password" name="password" placeholder="••••••••" class="input input-bordered w-full"
                        required />
                </div>

                @error('email')
                    <p class="text-error text-xs">{{ $message }}</p>
                @enderror

                <div class="form-control mt-6">
                    <button type="submit" class="btn btn-primary">Login</button>
                </div>
            </form>
        </div>
    </div>
</body>

</html>
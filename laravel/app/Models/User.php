<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use Notifiable;

    protected $fillable = [
        'email',
        'password',
        'is_active',
        'is_superuser',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];
}

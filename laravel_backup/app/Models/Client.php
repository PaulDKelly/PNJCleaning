<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Client extends Model
{
    use HasFactory;

    protected $fillable = ['client_name', 'company', 'address', 'portal_token', 'archived'];

    // If we establish strict relationship later:
    // public function sites() {
    //     return $this->hasMany(ClientSite::class, 'client_name', 'client_name');
    // }
}

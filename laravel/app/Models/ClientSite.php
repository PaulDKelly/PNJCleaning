<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ClientSite extends Model
{
    use HasFactory;

    protected $fillable = ['client_name', 'site_name', 'brand_name', 'archived'];

    public function client()
    {
        // Loose relationship via name
        return $this->belongsTo(Client::class, 'client_name', 'client_name');
    }
}

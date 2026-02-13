<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use App\Models\User;
use App\Models\Client;
use App\Models\ClientSite;

class DatabaseSeeder extends Seeder
{
    public function run()
    {
        // Create Admin User
        User::create([
            'email' => 'admin@pnjcleaning.co.uk',
            'password' => Hash::make('password123'),
            'is_superuser' => true,
        ]);

        // Create Seed Data (similar to Python seed)
        $client1 = Client::create([
            'client_name' => 'Adil Catering Ltd',
            'company' => 'Adil Catering',
            'portal_token' => 'adil123'
        ]);

        ClientSite::create(['client_name' => 'Adil Catering Ltd', 'site_name' => 'High St 1', 'brand_name' => 'Burger King']);
        ClientSite::create(['client_name' => 'Adil Catering Ltd', 'site_name' => 'Drive Thru 2', 'brand_name' => 'Burger King']);

        $client2 = Client::create([
            'client_name' => 'Stonegate Pubs',
            'company' => 'Stonegate Group',
            'portal_token' => 'stonegate123'
        ]);

        ClientSite::create(['client_name' => 'Stonegate Pubs', 'site_name' => 'Red Lion', 'brand_name' => 'Stonegate']);
        ClientSite::create(['client_name' => 'Stonegate Pubs', 'site_name' => 'Blue Boar', 'brand_name' => 'Stonegate']);

        $client3 = Client::create([
            'client_name' => 'Greene King',
            'company' => 'Greene King PLC',
            'portal_token' => 'gk123'
        ]);
        ClientSite::create(['client_name' => 'Greene King', 'site_name' => 'Kings Head', 'brand_name' => 'Greene King']);
    }
}

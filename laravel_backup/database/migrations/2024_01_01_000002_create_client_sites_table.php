<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up()
    {
        Schema::create('client_sites', function (Blueprint $table) {
            $table->id();
            // We use string FK to match legacy layout, or could use unsignedBigInteger if normalized.
            // Following existing pattern:
            $table->string('client_name')->index();
            $table->string('site_name');
            $table->string('brand_name')->nullable()->index();
            $table->boolean('archived')->default(false);
            $table->timestamps();

            // Foreign key logic if we normalized:
            // $table->foreignId('client_id')->constrained()->onDelete('cascade');
        });
    }

    public function down()
    {
        Schema::dropIfExists('client_sites');
    }
};

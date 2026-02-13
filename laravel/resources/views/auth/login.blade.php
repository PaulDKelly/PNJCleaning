@extends('layouts.app')

@section('content')
    <div class="flex items-center justify-center min-h-[calc(100vh-8rem)]">
        <div class="w-full max-w-md bg-white shadow-xl rounded-xl border border-slate-100 overflow-hidden">
            <div class="p-8">
                <div class="flex justify-center mb-6">
                    <img src="/logo.jpeg" alt="PNJ Cleaning" class="h-10 w-auto">
                </div>

                <form action="{{ route('login') }}" method="POST" class="space-y-5">
                    @csrf
                    <div class="flex flex-col space-y-1">
                        <label class="text-sm font-medium text-slate-600">Email</label>
                        <input type="email" name="email" placeholder="admin@pnjcleaning.co.uk"
                            class="w-full rounded-lg border-slate-300 border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            required />
                    </div>
                    <div class="flex flex-col space-y-1">
                        <label class="text-sm font-medium text-slate-600">Password</label>
                        <input type="password" name="password" placeholder="••••••••"
                            class="w-full rounded-lg border-slate-300 border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            required />
                    </div>

                    @error('email')
                        <p class="text-red-500 text-xs font-medium">{{ $message }}</p>
                    @enderror

                    <div class="pt-2">
                        <button type="submit"
                            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors shadow-sm">
                            Login
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
@endsection
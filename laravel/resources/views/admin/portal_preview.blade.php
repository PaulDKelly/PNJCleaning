@extends('layouts.app')

@section('content')
    <div class="space-y-8 pb-32">
        <!-- Header -->
        <div class="space-y-1">
            <div class="text-xs uppercase tracking-[0.2em] font-bold text-slate-400">Administration / Portal Experience
            </div>
            <h2 class="text-3xl font-bold text-slate-800">Portal Preview Selector</h2>
            <p class="text-slate-500">Pick a client to preview exactly what they see in their secure portal.</p>
        </div>

        <!-- Client Selection List -->
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 class="text-xl font-semibold text-slate-800 mb-6">Select Client Portfolio</h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                @forelse($clients as $c)
                    <a href="#"
                        class="p-6 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-slate-100 transition-all flex justify-between items-center group">
                        <div class="space-y-1">
                            <div class="font-bold text-slate-800 group-hover:text-blue-600 transition-colors text-lg">
                                {{ $c->client_name }}</div>
                            <div class="text-[10px] text-slate-400 uppercase font-bold">{{ $c->company ?? 'Independent' }}</div>
                        </div>
                        <div
                            class="bg-white p-2 rounded-lg shadow-sm group-hover:translate-x-1 transition-transform text-blue-600">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd"
                                    d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                                    clip-rule="evenodd" />
                            </svg>
                        </div>
                    </a>
                @empty
                    <div class="col-span-2 text-center py-12 text-slate-400 italic">No clients found in the system.</div>
                @endforelse
            </div>
        </div>
    </div>
@endsection
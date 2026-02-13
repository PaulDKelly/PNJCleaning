@foreach($sites as $s)
    <tr
        class="hover:bg-slate-50 group border-b border-slate-100 last:border-0 {{ $s->archived ? 'opacity-50 bg-slate-50' : '' }}">
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="font-bold text-slate-800">{{ $s->site_name }}</div>
            <div class="text-xs text-slate-500">{{ $s->address }}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 text-slate-600 bg-white">
                {{ $s->brand_name ?? 'Generic' }}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-slate-600">{{ $s->client_name }}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            @if($s->archived)
                <span
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Archived</span>
            @else
                <span
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>
            @endif
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <!-- Actions -->
            <button hx-get="{{ route('admin.sites.edit', $s->id) }}" hx-target="#edit-modal-container"
                class="text-blue-600 hover:text-blue-900 transition-colors">
                Edit
            </button>
        </td>
    </tr>
@endforeach
@foreach($clients as $c)
    <tr class="hover:bg-slate-50 group border-b border-slate-100 last:border-0">
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="font-bold text-slate-800">{{ $c->client_name }}</div>
            <div class="text-xs text-slate-500">{{ $c->company }}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <!-- Using a placeholder count or eager load relationship in controller -->
            <div
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                {{-- $c->sites->count() --}} N/A
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ $c->portal_token ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600' }}">
                {{ $c->portal_token ? 'Active' : 'No Access' }}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <button hx-get="{{ route('admin.clients.edit', $c->id) }}" hx-target="#edit-modal-container"
                class="text-blue-600 hover:text-blue-900 transition-colors">
                Edit
            </button>
        </td>
    </tr>
@endforeach
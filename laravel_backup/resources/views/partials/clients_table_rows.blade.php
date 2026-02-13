@foreach($clients as $c)
    <tr class="hover:bg-slate-50 group">
        <td>
            <div class="font-bold text-slate-700">{{ $c->client_name }}</div>
            <div class="text-xs text-slate-400">{{ $c->company }}</div>
        </td>
        <td>
            <!-- Using a placeholder count or eager load relationship in controller -->
            <div class="badge badge-sm badge-ghost">
                {{-- $c->sites->count() --}} N/A
            </div>
        </td>
        <td>
            <span class="badge badge-sm {{ $c->portal_token ? 'badge-success text-white' : 'badge-ghost' }}">
                {{ $c->portal_token ? 'Active' : 'No Access' }}
            </span>
        </td>
        <td class="text-right">
            <button class="btn btn-xs btn-ghost text-slate-400">Edit</button>
        </td>
    </tr>
@endforeach
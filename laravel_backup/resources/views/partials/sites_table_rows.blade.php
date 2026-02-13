@foreach($sites as $s)
    <tr class="hover:bg-slate-50 group {{ $s->archived ? 'opacity-50 bg-slate-100' : '' }}">
        <td>
            <div class="font-bold text-slate-700">{{ $s->site_name }}</div>
            <div class="text-xs text-slate-400">{{ $s->address }}</div>
        </td>
        <td>
            <span class="badge badge-outline badge-sm">{{ $s->brand_name ?? 'Generic' }}</span>
        </td>
        <td>
            <div class="text-sm">{{ $s->client_name }}</div>
        </td>
        <td>
            @if($s->archived)
                <span class="badge badge-sm badge-warning">Archived</span>
            @else
                <span class="badge badge-sm badge-success text-white">Active</span>
            @endif
        </td>
        <td class="text-right">
            <!-- Actions -->
            <button class="btn btn-xs btn-ghost">Edit</button>
        </td>
    </tr>
@endforeach
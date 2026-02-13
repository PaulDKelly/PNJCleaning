<div id="edit-client-modal-{{ $client->id }}"
    class="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center backdrop-blur-sm">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6 transform transition-all">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-bold text-slate-800">Edit Client: {{ $client->client_name }}</h3>
            <button onclick="document.getElementById('edit-client-modal-{{ $client->id }}').remove()"
                class="text-slate-400 hover:text-slate-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24"
                    stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
        <form action="{{ route('admin.clients.update', $client->id) }}" method="POST" class="space-y-4">
            @csrf
            @method('PUT')
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Client Name</label>
                <input type="text" name="client_name" value="{{ $client->client_name }}" required
                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Company / Group</label>
                <input type="text" name="company" value="{{ $client->company }}" placeholder="Optional"
                    class="w-full rounded-lg border-slate-300 focus:border-blue-500 focus:ring-blue-500 text-sm">
            </div>

            <div class="flex items-center gap-2 mt-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
                <input type="checkbox" name="archived" id="archive-client-check-{{ $client->id }}"
                    class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4" {{ $client->archived ? 'checked' : '' }}>
                <label for="archive-client-check-{{ $client->id }}" class="text-sm font-medium text-slate-700">Archive
                    this client</label>
            </div>
            <div class="pt-4 flex justify-end gap-3">
                <button type="button" onclick="document.getElementById('edit-client-modal-{{ $client->id }}').remove()"
                    class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors">Cancel</button>
                <button type="submit"
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">Save
                    Changes</button>
            </div>
        </form>
    </div>
</div>
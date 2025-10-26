import { Shield } from 'lucide-react';

export function AdminBadge() {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/20 border border-yellow-500/30 rounded-md" data-testid="badge-admin">
      <Shield className="text-yellow-600" size={16} />
      <span className="text-sm font-medium text-yellow-700">Admin</span>
    </div>
  );
}

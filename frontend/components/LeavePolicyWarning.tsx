export function LeavePolicyWarningBadge({ warning }: { warning?: string | null }) {
  if (!warning) return null;
  return (
    <span
      className="ml-1 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900 dark:text-amber-300"
      title={warning}
    >
      Exceeds max
    </span>
  );
}

export function LeavePolicyWarningBanner({ warning }: { warning: string }) {
  return (
    <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
      {warning}
    </p>
  );
}

import { AppShell } from "@/components/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { RequireAuth } from "@/components/RequireAuth";

export default function ProtectedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <RequireAuth>
      <ErrorBoundary>
        <AppShell>{children}</AppShell>
      </ErrorBoundary>
    </RequireAuth>
  );
}

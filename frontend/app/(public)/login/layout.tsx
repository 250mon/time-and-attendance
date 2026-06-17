export default function LoginLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 px-6 py-12 dark:bg-slate-950">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}

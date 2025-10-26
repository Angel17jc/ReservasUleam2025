import { ReactNode, CSSProperties } from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { Navbar } from '@/components/Navbar';

export function UserLayout({ children }: { children: ReactNode }) {
  const style: CSSProperties = {
    '--sidebar-width': '18rem',
    '--sidebar-width-icon': '4rem',
  };

  return (
    <SidebarProvider style={style}>
      <div className="flex h-screen w-full">
        <AppSidebar variant="user" />
        <div className="flex flex-col flex-1 overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-auto bg-background">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
}

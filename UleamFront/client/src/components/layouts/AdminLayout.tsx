import { ReactNode, CSSProperties, useRef } from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { Navbar } from '@/components/Navbar';
import { ChatWidget, type ChatWidgetRef } from '@/components/chat/ChatWidget';
import { useAuth } from '@/contexts/AuthContext';

export function AdminLayout({ children }: { children: ReactNode }) {
  const chatWidgetRef = useRef<ChatWidgetRef>(null);

  const handleOpenChat = () => {
    chatWidgetRef.current?.open();
  };

  const style: CSSProperties = {
    '--sidebar-width': '18rem',
    '--sidebar-width-icon': '4rem',
  };

  const { isAdmin } = useAuth();

  return (
    <SidebarProvider style={style} defaultOpen={isAdmin ? true : undefined}>
      <div className="flex h-screen w-full">
        <AppSidebar variant="admin" onOpenChat={handleOpenChat} />
        <div className="flex flex-col flex-1 overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-auto bg-background">{children}</main>
        </div>
        
        {/* AI Chat Widget - Controlled by sidebar button */}
        <ChatWidget ref={chatWidgetRef} position="bottom-right" defaultOpen={false} hideFloatingButton={true} />
      </div>
    </SidebarProvider>
  );
}

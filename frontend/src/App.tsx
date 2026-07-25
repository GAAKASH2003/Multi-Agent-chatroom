import { useState } from "react";
import { AuthPage } from "./pages/AuthPage";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { ManageModal } from "./components/ManageModal";
import { useStore } from "./lib/store";
import {Group,Character} from "./lib/types";
import { Toaster } from './components/ui/sonner';

function App() {
  const store = useStore();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeGroupId, setActiveGroupId] = useState<string | null>(null);
  const [manageOpen, setManageOpen] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [editGroup, setEditGroup] = useState<Group | null>(null);
  const [editCharacter, setEditCharacter] = useState<Character | null>(null);
  
  const token =
    typeof window !== "undefined"
      ? (localStorage.getItem("auth_token") ?? "")
      : "";

  if (!store.user) {
    return <AuthPage onLogin={store.login} />;
  }

  const activeSession =
    store.sessions.find((s) => s.id === activeSessionId) || null;
  const activeGroup = store.groups.find(
    (g) => g.id === activeGroupId || g.id === activeSession?.groupId,
  );
  

  const handleSelectSession = async (sessionId: string, groupId: string) => {
    setActiveSessionId(sessionId);
    setActiveGroupId(groupId);
    setMobileSidebarOpen(false);
    await store.loadSessionMessages(sessionId);
  };

  const handleCreateSession = async (groupId: string, title: string) => {
    const session = await store.createSession(groupId, title);
    if (session) {
      setActiveSessionId(session.id);
      setActiveGroupId(groupId);
      await store.loadSessionMessages(session.id);
    }
  };

  const handleEditGroup = (group: Group) => {
      setEditGroup(group);
      setManageOpen(true);
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden">
      {/* Sidebar - desktop */}
      <div className="hidden md:flex w-80 shrink-0">
        <Sidebar
          groups={store.groups}
          sessions={store.sessions}
          user={store.user}
          activeSessionId={activeSessionId}
          activeGroupId={activeGroupId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onDeleteSession={store.deleteSession}
          onOpenGroups={() => setManageOpen(true)}
          onOpenCharacters={() => setManageOpen(true)}
          onLogout={store.logout}
        />
      </div>

      {/* Sidebar - mobile drawer */}
      {mobileSidebarOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <div className="relative w-80 max-w-[85vw] z-10">
            <Sidebar
              groups={store.groups}
              sessions={store.sessions}
              user={store.user}
              activeSessionId={activeSessionId}
              activeGroupId={activeGroupId}
              onSelectSession={handleSelectSession}
              onCreateSession={handleCreateSession}
              onDeleteSession={store.deleteSession}
              onOpenGroups={() => setManageOpen(true)}
              onOpenCharacters={() => setManageOpen(true)}
              onLogout={store.logout}
            />
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex relative">
        {/* Mobile top bar */}
        <div className="md:hidden absolute top-0 left-0 right-0 z-20 glass border-b border-border px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="flex items-center gap-2 text-primary"
          >
            <div className="h-8 w-8 rounded-lg bg-primary/15 border border-primary/40 flex items-center justify-center">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </div>
            <span className="font-bold text-primary">NeonChat</span>
          </button>
        </div>

        <div className="flex-1 flex pt-12 md:pt-0">
          <ChatView
            session={activeSession}
            group={activeGroup}
            characters={store.characters}
            liveTurns={store.liveTurns}
            streamingIds={store.streamingIds}
            onSend={store.sendMessage}
            token={token}
            onEditGroup={(g) => {
              handleEditGroup(g);
            }}

          />
        </div>
      </div>

      <ManageModal
        open={manageOpen}
        onOpenChange={setManageOpen}
        groups={store.groups}
        characters={store.characters}
        onAddGroup={store.addGroup}
        onUpdateGroup={store.updateGroup}
        onDeleteGroup={store.deleteGroup}
        onAddCharacter={store.addCharacter}
        onUpdateCharacter={store.updateCharacter}
        onDeleteCharacter={store.deleteCharacter}
        onEditConsumed={() => {
          setEditGroup(null);
        }}
        scopeGroupId={activeGroupId}
      />
       <Toaster position="bottom-right" richColors closeButton />
    </div>
  );
}

export default App;

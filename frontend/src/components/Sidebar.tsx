import { useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  MessageSquare,
  Plus,
  Search,
  Users,
  Settings,
  LogOut,
  Trash2,
  ChevronRight,
} from "lucide-react";
import type { Group, ChatSession, User } from "@/lib/types";

interface SidebarProps {
  groups: Group[];
  sessions: ChatSession[];
  user: User;
  activeSessionId: string | null;
  activeGroupId: string | null;
  onSelectSession: (sessionId: string, groupId: string) => void;
  onCreateSession: (groupId: string, title: string) => Promise<unknown>;
  onDeleteSession: (sessionId: string) => Promise<void> | void;
  onOpenGroups: () => void;
  onOpenCharacters: () => void;
  onLogout: () => void;
}

export function Sidebar({
  groups,
  sessions,
  user,
  activeSessionId,
  activeGroupId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onOpenGroups,
  onOpenCharacters,
  onLogout,
}: SidebarProps) {
  const [query, setQuery] = useState("");
  const [newSessionGroup, setNewSessionGroup] = useState<string | null>(null);
  const [newSessionTitle, setNewSessionTitle] = useState("");

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(query.toLowerCase()),
  );

  const sessionsByGroup = (groupId: string) =>
    filteredSessions
      .filter((s) => s.groupId === groupId)
      .sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-primary/15 border border-primary/40 flex items-center justify-center">
              <MessageSquare className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-lg font-bold text-primary">GenChat</h1>
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={onOpenCharacters}
              title="Characters"
            >
              <Settings className="h-4 w-4 text-muted-foreground" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onOpenGroups}
              title="Groups"
            >
              <Users className="h-4 w-4 text-muted-foreground" />
            </Button>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search sessions..."
            className="pl-9 bg-background/50"
          />
        </div>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto scrollbar-neon p-2">
        {groups.map((group) => {
          const groupSessions = sessionsByGroup(group.id);
          const isActiveGroup = activeGroupId === group.id;
          return (
            <div key={group.id} className="mb-2">
              <div className="flex items-center justify-between px-2 py-1.5">
                <div className="flex items-center gap-2 min-w-0">
                  <Users className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider truncate">
                    {group.name}
                  </span>
                </div>
                <Dialog
                  open={newSessionGroup === group.id}
                  onOpenChange={(o) => {
                    setNewSessionGroup(o ? group.id : null);
                    setNewSessionTitle("");
                  }}
                >
                  <DialogTrigger asChild>
                    <button
                      className="text-muted-foreground hover:text-primary transition-colors"
                      title="New session"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </DialogTrigger>
                  <DialogContent className="glass">
                    <DialogHeader>
                      <DialogTitle>New session in {group.name}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-2 py-2">
                      <Label htmlFor="session-title">Session title</Label>
                      <Input
                        id="session-title"
                        value={newSessionTitle}
                        onChange={(e) => setNewSessionTitle(e.target.value)}
                        placeholder="e.g. Brainstorming ideas"
                        autoFocus
                      />
                    </div>
                    <DialogFooter>
                      <Button
                        onClick={async () => {
                          if (newSessionTitle.trim()) {
                            await onCreateSession(
                              group.id,
                              newSessionTitle.trim(),
                            );
                            setNewSessionGroup(null);
                            setNewSessionTitle("");
                          }
                        }}
                        className="bg-primary hover:bg-primary/90 text-primary-foreground"
                      >
                        Create
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>

              <div className={isActiveGroup ? "space-y-0.5" : "space-y-0.5"}>
                {groupSessions.length === 0 && (
                  <p className="text-xs text-muted-foreground px-3 py-2 italic">
                    No sessions yet
                  </p>
                )}
                {groupSessions.map((session) => {
                  const active = activeSessionId === session.id;
                  return (
                    <div
                      key={session.id}
                      className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
                        active
                          ? "bg-primary/10 border border-primary/40"
                          : "hover:bg-background/50"
                      }`}
                      onClick={() => onSelectSession(session.id, group.id)}
                    >
                      <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center shrink-0">
                        <MessageSquare
                          className={`h-4 w-4 ${active ? "text-primary" : "text-muted-foreground"}`}
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm font-medium truncate ${active ? "text-primary" : "text-foreground"}`}
                        >
                          {session.title}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {new Date(session.updatedAt).toLocaleDateString([], {
                            month: "short",
                            day: "numeric",
                          })}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          void onDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      {active && (
                        <ChevronRight className="h-4 w-4 text-primary" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* User footer */}
      <div className="p-3 border-t border-border flex items-center gap-3">
        <Avatar className="h-9 w-9">
          <AvatarImage src={user.avatar} />
          <AvatarFallback className="bg-primary/15 text-primary text-xs">
            {user.name.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{user.name}</p>
          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onLogout} title="Sign out">
          <LogOut className="h-4 w-4 text-muted-foreground" />
        </Button>
      </div>
    </div>
  );
}

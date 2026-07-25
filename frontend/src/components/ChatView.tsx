import { useEffect, useRef, useState, useCallback } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Users, Info, Loader2 } from "lucide-react";
import type {
  Character,
  ChatSession,
  Group,
  Message,
  ConvTurn,
} from "@/lib/types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface ChatViewProps {
  session: ChatSession | null;
  group: Group | undefined;
  characters: Character[];
  liveTurns: ConvTurn[]; // ← streaming turns from parent
  streamingIds: string[];
  onSend: (sessionId: string, content: string) => void;
  onEditGroup: (group: Group) => void;
  token: string;
}

const COLORS = ["cyan", "green", "pink", "purple", "blue", "yellow"] as const;
type Color = (typeof COLORS)[number];

const colorClasses: Record<
  Color,
  { bubble: string; text: string; ring: string }
> = {
  cyan: {
    bubble: "bg-sky-500/10 border-sky-400/25",
    text: "text-sky-400",
    ring: "ring-sky-400/30",
  },
  green: {
    bubble: "bg-teal-500/10 border-teal-400/25",
    text: "text-teal-400",
    ring: "ring-teal-400/30",
  },
  pink: {
    bubble: "bg-rose-500/10 border-rose-400/25",
    text: "text-rose-400",
    ring: "ring-rose-400/30",
  },
  purple: {
    bubble: "bg-violet-500/10 border-violet-400/25",
    text: "text-violet-400",
    ring: "ring-violet-400/30",
  },
  blue: {
    bubble: "bg-blue-500/10 border-blue-400/25",
    text: "text-blue-400",
    ring: "ring-blue-400/30",
  },
  yellow: {
    bubble: "bg-amber-500/10 border-amber-400/25",
    text: "text-amber-400",
    ring: "ring-amber-400/30",
  },
};

function hashColor(name: string): Color {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return COLORS[Math.abs(h) % COLORS.length];
}

// ── Message bubble ────────────────────────────────────────────────

function StreamingText({ text }: { text: string }) {
  const [visible, setVisible] = useState("");

  useEffect(() => {
    let i = 0;

    const timer = setInterval(() => {
      i++;

      setVisible(text.slice(0, i));

      if (i >= text.length) {
        clearInterval(timer);
      }
    }, 45);

    return () => clearInterval(timer);
  }, [text]);

  return <span>{visible}</span>;
}

function MessageBubble({
  msg,
  charById,
  streamingIds,
}: {
  msg: Message;
  charById: (id: string | null) => Character | undefined;
  streamingIds: string[];
}) {
  const isUser = msg.role === "user";
  const character = charById(msg.characterId ?? null);
  const colorKey = character ? hashColor(character.name) : "cyan";
  const cc = colorClasses[colorKey];
  const isStreaming = streamingIds.includes(msg.id);

  return (
    <div
      className={`flex items-end gap-2 animate-fade-in-up ${isUser ? "justify-start" : "justify-end"}`}
    >
      {!isUser && (
        <Avatar className={`h-8 w-8 shrink-0 ring-2 ${cc.ring}`}>
          <AvatarImage src={character?.avatar} />
          <AvatarFallback className={`text-[10px] ${cc.text} bg-background`}>
            {(character?.name ?? "??").slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={`max-w-[75%] flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}
      >
        {!isUser && character && (
          <span className={`text-xs font-medium ${cc.text} px-1`}>
            {character.name}
          </span>
        )}
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed border ${
            isUser
              ? "bg-primary/15 border-primary/30 text-foreground rounded-br-sm"
              : `${cc.bubble} text-foreground rounded-bl-sm`
          }`}
        >
          {
            <span>{msg.content}</span>
          }
        </div>
        <span className="text-[10px] text-muted-foreground px-1">
          {new Date(msg.createdAt).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
}

// ── Turn block: query + its responses ────────────────────────────
function TurnBlock({
  turn,
  isLast,
  charById,
  streamingIds,
}: {
  turn: ConvTurn;
  isLast: boolean;
  charById: (id: string | null) => Character | undefined;
  streamingIds: string[];
}) {
  const isPending = turn.conv_id.startsWith("pending-");
  const pendingQueryId = `${turn.conv_id}-query`;
  return (
    <div className="space-y-2">
      {/* User query */}
      <MessageBubble
        msg={turn.query}
        charById={charById}
        streamingIds={streamingIds}
      />

      {/* Lightweight loading indicator for pending turns */}
      {isPending && streamingIds.includes(pendingQueryId) && (
        <div className="pl-4">
          <div className="text-sm text-muted-foreground flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <span>Responses loading…</span>
          </div>
        </div>
      )}

      {/* Character responses indented slightly */}
      {turn.responses.length > 0 && (
        <div className="space-y-2 pl-2 border-l-2 border-border/30 ml-1">
          {turn.responses.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              charById={charById}
              streamingIds={streamingIds}
            />
          ))}
        </div>
      )}

      {/* Divider between turns */}
      {!isLast && (
        <div className="flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-border/25" />
        </div>
      )}
    </div>
  );
}

// ── Main ChatView ─────────────────────────────────────────────────
export function ChatView({
  session,
  group,
  characters,
  liveTurns,
  streamingIds,
  onSend,
  token,
  onEditGroup,
}: ChatViewProps) {
  const [input, setInput] = useState("");
  const [historyTurns, setHistoryTurns] = useState<ConvTurn[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load history on session change
  const loadHistory = useCallback(
    async (sessionId: string) => {
      setHistoryLoading(true);
      setHistoryTurns([]);
      try {
        const res = await fetch(`${BASE_URL}/conv/session/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setHistoryTurns(data.turns ?? []);
      } catch (e) {
        console.error("Failed to load history", e);
      } finally {
        setHistoryLoading(false);
      }
    },
    [token],
  );

  useEffect(() => {
    if (!session) {
      setHistoryTurns([]);
      return;
    }
    loadHistory(session.id);
  }, [session?.id, loadHistory]);

  // Merge history + live turns, overriding history with any newer live turn updates.
  const liveTurnMap = new Map(liveTurns.map((turn) => [turn.conv_id, turn]));
  const mergedHistory = historyTurns.map(
    (turn) => liveTurnMap.get(turn.conv_id) ?? turn,
  );
  const addedLiveTurns = liveTurns.filter(
    (turn) => !historyTurns.some((history) => history.conv_id === turn.conv_id),
  );
  const allTurns = [...mergedHistory, ...addedLiveTurns].sort(
    (a, b) => a.seq_num - b.seq_num,
  );

  // Auto scroll
  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [allTurns.length, streamingIds.length]);

  const charById = (id: string | null) =>
    id ? characters.find((c) => c.id === id) : undefined;

  const handleSend = () => {
    if (!session || !input.trim()) return;
    onSend(session.id, input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!session) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center chat-bg gap-4">
        <div className="h-20 w-20 rounded-2xl bg-primary/15 border border-primary/40 flex items-center justify-center animate-pulse-soft">
          <Users className="h-10 w-10 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-primary">Select a session</h2>
        <p className="text-muted-foreground text-center max-w-sm">
          Pick a session from the sidebar or create a new one to start chatting.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col chat-bg overflow-hidden">
      {/* Header */}
      <div className="glass border-b border-border px-4 py-3 flex items-center gap-3 shrink-0">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
          <Users className="h-5 w-5 text-primary" />
        </div>
        <div
          className="flex-1 min-w-0"
          onClick={() => group && onEditGroup(group)}
        >
          <h2 className="font-semibold truncate">{session.title}</h2>
          <p className="text-xs text-muted-foreground truncate">
            {group?.name} · {group?.characterIds.length} member
            {characters.length !== 1 ? "s" : ""}
          </p>
        </div>
        {/* <div className="flex -space-x-2">
          {characters.slice(0, 5).map((c) => {
            const cc = colorClasses[hashColor(c.name)];
            return (
              <Avatar
                key={c.id}
                className={`h-7 w-7 ring-2 ${cc.ring} ring-offset-0`}
              >
                <AvatarImage src={c.avatar} />
                <AvatarFallback
                  className={`text-[10px] ${cc.text} bg-background`}
                >
                  {c.name.slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            );
          })}
          {characters.length > 5 && (
            <div className="h-7 w-7 rounded-full bg-muted border-2 border-background flex items-center justify-center text-[10px] text-muted-foreground">
              +{characters.length - 5}
            </div>
          )}
        </div> */}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-neon px-4 py-6"
      >
        {historyLoading ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              Loading conversation…
            </p>
          </div>
        ) : allTurns.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
            <Info className="h-8 w-8 text-muted-foreground" />
            <p className="text-muted-foreground text-sm">
              Send a message to start the conversation.
            </p>
          </div>
        ) : (
          <div className="space-y-4  mx-auto">
            {allTurns.map((turn, ti) => (
              <TurnBlock
                key={turn.conv_id}
                turn={turn}
                isLast={ti === allTurns.length - 1}
                charById={charById}
                streamingIds={streamingIds}
              />
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="glass border-t border-border p-4 shrink-0">
        <div className="flex items-end gap-2 max-w-3xl mx-auto">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
            rows={1}
            className="resize-none bg-background/50 min-h-[44px] max-h-32 scrollbar-neon"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || streamingIds.length > 0}
            size="icon"
            className="h-11 w-11 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shrink-0"
          >
            {streamingIds.length > 0 ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

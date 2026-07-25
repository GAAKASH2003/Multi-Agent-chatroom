import { useState, useCallback, useEffect } from "react";
import type {
  Character,
  Group,
  ChatSession,
  Message,
  User,
  ConvTurn,
} from "./types";
import {
  seedCharacters,
  seedGroups,
  seedSessions,
  seedMessages,
} from "./mock-data";
import { toast } from 'sonner';


const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STORAGE_KEY = "neon-chat-state-v1";
const USER_KEY = "neon-chat-user-v1";
const AUTH_TOKEN_KEY = "auth_token";

interface PersistState {
  characters: Character[];
  groups: Group[];
  sessions: ChatSession[];
  messages: Message[];
}

function loadState(): PersistState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return {
    characters: seedCharacters,
    groups: seedGroups,
    sessions: seedSessions,
    messages: seedMessages,
  };
}

export function useStore() {
  const [state, setState] = useState<PersistState>(loadState);
  const [liveTurns, setLiveTurns] = useState<ConvTurn[]>([]);
  const [user, setUser] = useState<User | null>(() => {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [streamingIds, setStreamingIds] = useState<string[]>([]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // ignore
    }
  }, [state]);

  useEffect(() => {
    try {
      if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
      else localStorage.removeItem(USER_KEY);
    } catch {
      // ignore
    }
  }, [user]);

  useEffect(() => {
    if (liveTurns.length === 0) return;

    setState((s) => {
      const existingIds = new Set(s.messages.map((m) => m.id));
      const incomingMessages = liveTurns
        .flatMap((turn: ConvTurn) => [turn.query, ...turn.responses])
        .filter((message) => !existingIds.has(message.id));

      if (incomingMessages.length === 0) return s;

      return {
        ...s,
        messages: [...s.messages, ...incomingMessages],
      };
    });
  }, [liveTurns]);

  const login = useCallback(
    (authUser: {
      email: string;
      name: string;
      id?: string;
      token?: string;
    }) => {
      setUser({
        id: authUser.id || crypto.randomUUID(),
        email: authUser.email,
        name: authUser.name,
        avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(authUser.name)}`,
      });

      try {
        if (authUser.token)
          localStorage.setItem(AUTH_TOKEN_KEY, authUser.token);
        else localStorage.removeItem(AUTH_TOKEN_KEY);
      } catch {

      }
    },
    [],
  );

  const logout = useCallback(() => {
    setUser(null);
  
    try {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const fetchGroupsAndCharacters = useCallback(async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token || !user?.id) return;

    try {
      const [groupsRes, charactersRes] = await Promise.all([
        fetch(`${API_BASE_URL}/group/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/character/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (groupsRes.ok) {
        const groupData = await groupsRes.json();
        const mergedGroups = [
          ...(groupData.seed_groups || []).map((g: any) => ({
            id: g.id,
            name: g.name,
            description: g.description,
            characterIds: g.characters || [],
            createdAt: Date.now(),
            grpType: "seed" as const,
          })),
          ...(groupData.custom_groups || []).map((g: any) => ({
            id: g.id,
            name: g.name,
            description: g.description,
            characterIds: g.characters || [],
            createdAt: Date.now(),
            grpType: "custom" as const,
          })),
        ];
        setState((s) => ({ ...s, groups: mergedGroups }));
      }

      if (charactersRes.ok) {
        const characterData = await charactersRes.json();
        const mappedCharacters = (characterData || []).map((c: any) => ({
          id: c.id,
          name: c.name,
          type: c.type,
          avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(c.name)}`,
          persona: c.description || "",
          color: "cyan" as const,
        }));
        setState((s) => ({ ...s, characters: mappedCharacters }));
      }
    } catch {
      // ignore
    }
  }, [user]);

  const fetchSessionsForGroups = useCallback(async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token || !user?.id) return;

    try {
      const groupsToLoad = state.groups.filter((g) => g.id);

      const sessionResults = await Promise.all(
        groupsToLoad.map(async (group) => {
          console.log(group.id)
          const response = await fetch(
            `${API_BASE_URL}/session/list/${group.id}`,
            {
              headers: { Authorization: `Bearer ${token}` },
            },
          );
          if (!response.ok) return [];
          const data = await response.json();
          return (data.sessions || []).map((s: any) => ({
            id: s.session_id,
            groupId: group.id,
            title: s.title || "New Chat",
            createdAt: new Date(s.created_at || Date.now()).getTime(),
            updatedAt: new Date(
              s.updated_at || s.created_at || Date.now(),
            ).getTime(),
            memorySummary: s.memory_summary,
            convIds: s.conv_ids || [],
          }));
        }),
      );

      const allSessions = sessionResults.flat();
      if (allSessions.length > 0) {
        setState((s) => ({ ...s, sessions: allSessions }));
      }
    } catch {
      // ignore
    }
  }, [state.groups, user]);

  useEffect(() => {
    fetchGroupsAndCharacters();
  }, [fetchGroupsAndCharacters]);

  useEffect(() => {
    if (state.groups.length > 0) {
      fetchSessionsForGroups();
    }
  }, [state.groups, fetchSessionsForGroups]);

  const addGroup = useCallback(
    (name: string, description: string, characterIds: string[]) => {
      (async () => {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        // try server create first
        if (token) {
          try {
            const res = await fetch(`${API_BASE_URL}/group/`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({ name, description }),
            });

            if (res.ok) {
              const body = await res.json();
              const created: Group = {
                id: body.id,
                name: body.name,
                description: body.description,
                characterIds: body.characters || [],
                createdAt: Date.now(),
              };
              setState((s) => ({ ...s, groups: [...s.groups, created] }));

              // attach any selected characters to the new group on the server
              

              if ((characterIds || []).length > 0) {
                await Promise.all(
                  characterIds.map((charId) =>
                    fetch(`${API_BASE_URL}/group/addCharacter`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                      },
                      body: JSON.stringify({
                        group_id: created.id,
                        character_id: charId,
                      }),
                    }).catch(() => undefined),
                  ),
                );
                // locally update group's characterIds
                setState((s) => ({
                  ...s,
                  groups: s.groups.map((g) =>
                    g.id === created.id
                      ? { ...g, characterIds: characterIds }
                      : g,
                  ),
                }));
                toast.success('Group created', { description: `"${name}" is ready to go.` });
              }

              return;
            }
          } catch {
            // fall through to local-only create
          }
        }

        // fallback: create locally
        const group: Group = {
          id: crypto.randomUUID(),
          name,
          description,
          characterIds,
          createdAt: Date.now(),
        };
        setState((s) => ({ ...s, groups: [...s.groups, group] }));
        return group;
      })();
    },
    [],
  );


const updateGroup = useCallback(
  async (
    groupId: string,
    name: string,
    description: string,
    characterIds: string[],
  ): Promise<{ success: boolean; error?: string }> => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return { success: false, error: "Not authenticated" };

    try {
      const res = await fetch(`${API_BASE_URL}/group/${groupId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, description, character_ids: characterIds }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Request failed" }));
        return { success: false, error: err.detail || "Failed to update group" };
      }

      const body = await res.json();
      setState((s) => ({
        ...s,
        groups: s.groups.map((g) =>
          g.id === groupId
            ? { ...g, name: body.name, description: body.description, characterIds }
            : g
        ),
      }));
      toast.success('Group updated', { description: `"${name}" has been saved.` });
      return { success: true };

    } catch (err) {
      return { success: false, error: "Network error — please try again" };
    }
  },
  [],
);



  const deleteGroup = useCallback((groupId: string) => {
    setState((s) => {
      const sessionIds = s.sessions
        .filter((x) => x.groupId === groupId)
        .map((x) => x.id);
      return {
        ...s,
        groups: s.groups.filter((g) => g.id !== groupId),
        sessions: s.sessions.filter((x) => x.groupId !== groupId),
        messages: s.messages.filter((m) => !sessionIds.includes(m.sessionId)),
      };
    });
    toast.success('Group deleted', { description: 'The group and its sessions were removed.' });
  }, []);

const addCharacter = useCallback(
  async (
    name: string,
    persona: string,
    color: Character["color"],
    traits: string[],
  ): Promise<Character> => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    if (token) {
      try {
        const res = await fetch(`${API_BASE_URL}/character/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name,
            description: persona,
            traits,
          }),
        });

        if (res.ok) {
          const body = await res.json();

          const created: Character = {
            id: body.id,
            name: body.name,
            avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(body.name)}`,
            persona: body.description || persona,
            traits: body.traits || traits,
            color,
          };

          setState((s) => ({
            ...s,
            characters: [...s.characters, created],
          }));

          return created;
        }
      } catch {
        // fall through
      }
    }

    const created: Character = {
      id: crypto.randomUUID(),
      name,
      avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(name)}`,
      persona,
      traits,
      color,
    };

    setState((s) => ({
      ...s,
      characters: [...s.characters, created],
    }));

    toast.success("Character created", {
      description: `"${name}" joined the roster.`,
    });

    return created;
  },
  []
);

  const updateCharacter = useCallback(
    (
      characterId: string,
      name: string,
      persona: string,
      color: Character["color"],
      traits: string[],
    ) => {
      setState((s) => ({
        ...s,
        characters: s.characters.map((c) =>
          c.id === characterId
            ? {
                ...c,
                name,
                persona,
                color,
                traits,
                avatar:
                  c.name === name
                    ? c.avatar
                    : `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(name)}`,
              }
            : c,
        ),
      }));
      toast.success('Character updated', { description: `"${name}" has been saved.` });
    },
    [],
  );

  const deleteCharacter = useCallback((characterId: string) => {
    (async () => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        try {
          const res = await fetch(`${API_BASE_URL}/character/${characterId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          });
          toast.success('Character deleted', { description: 'The character was removed from all groups.' });
          if (!res.ok){
              toast.error('Failed to delete character on server', { description: 'The character was removed locally, but the server request failed.' });
          };
        } catch {
          // ignore server failure and continue to remove locally
          toast.error('Failed to delete character on server', { description: 'The character was removed locally, but the server request failed.' });
        }
      }

      setState((s) => ({
        ...s,
        characters: s.characters.filter((c) => c.id !== characterId),
        groups: s.groups.map((g) => ({
          ...g,
          characterIds: g.characterIds.filter((id) => id !== characterId),
        })),
      }));
    })();
  }, []);

  const createSession = useCallback(async (groupId: string, title: string) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/session/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ grp_id: groupId, title }),
      });

      if (!response.ok) throw new Error("Failed to create session");
      const created = await response.json();
      const session: ChatSession = {
        id: created.session_id,
        groupId,
        title: created.title || title,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        memorySummary: created.memory_summary || "",
        convIds: created.conv_ids || [],
      };
      setState((s) => ({ ...s, sessions: [session, ...s.sessions] }));
      return session;
    } catch {
      return null;
    }
  }, []);

  const loadSessionMessages = useCallback(async (sessionId: string) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/conv/session/${sessionId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (!response.ok) return;

      const data = await response.json();
      console.log("Fetched session messages:", data);
      const fetchedTurns = (data.turns || []).map(
        (turn: any, index: number) =>
          ({
            conv_id: turn.conv_id || `turn-${sessionId}-${index}`,
            seq_num: Number(turn.seq_num ?? index + 1),
            query: {
              id: turn.query?.id || `user-${sessionId}-${index}`,
              sessionId,
              characterId: null,
              role: "user",
              content: turn.query?.content || "",
              createdAt: Number(turn.query?.createdAt) || Date.now() + index,
            } as Message,
            responses: (turn.responses || []).map(
              (response: any, responseIndex: number) =>
                ({
                  id:
                    response.id ||
                    `response-${sessionId}-${index}-${responseIndex}`,
                  sessionId,
                  characterId: response.characterId || null,
                  role: "assistant",
                  content: response.content || "",
                  createdAt:
                    Number(response.createdAt) ||
                    Date.now() + index + responseIndex,
                }) as Message,
            ),
          }) as ConvTurn,
      );
      console.log("Fetched session messages:", fetchedTurns);
      setLiveTurns(fetchedTurns);
      setState((s) => ({
        ...s,
        messages: [
          ...s.messages.filter((m) => m.sessionId !== sessionId),
          ...fetchedTurns.flatMap((turn: ConvTurn) => [
            turn.query,
            ...turn.responses,
          ]),
        ],
      }));
    } catch {
      // ignore
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/session/${sessionId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to delete session");
    } catch {
      // ignore
    }

    setState((s) => ({
      ...s,
      sessions: s.sessions.filter((x) => x.id !== sessionId),
      messages: s.messages.filter((m) => m.sessionId !== sessionId),
    }));
  }, []);
  
  
function normalizeMarkdown(text:String): string {
  return text
    .replace(/\s*•\s*/g, "\n- ")
    .replace(/:\n-/g, ":\n\n- ")
    .replace(/\. ([A-Z])/g, ".\n\n$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

  const sendMessage = useCallback(
    async (sessionId: string, content: string) => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (!token) return;

      const group = state.groups.find((g) =>
        state.sessions.some((x) => x.id === sessionId && x.groupId === g.id),
      );

      if (!group) return;

      const pendingTurnId = `pending-${sessionId}-${Date.now()}`;
      const pendingQueryId = `${pendingTurnId}-query`;

      setStreamingIds([pendingQueryId]);

      // create a pending turn so the UI shows the query immediately
      const pendingTurn: ConvTurn = {
        conv_id: pendingTurnId,
        seq_num: Date.now(),
        query: {
          id: pendingQueryId,
          sessionId,
          characterId: null,
          role: "user",
          content,
          createdAt: Date.now(),
        },
        responses: [],
      };

      setLiveTurns((cur) => [...cur, pendingTurn]);

      // update session timestamp only
      setState((s) => ({
        ...s,
        sessions: s.sessions.map((x) =>
          x.id === sessionId ? { ...x, updatedAt: Date.now() } : x,
        ),
      }));

      try {
        const response = await fetch(`${API_BASE_URL}/conv/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            query: content,
            group_id: group.id,
            session_id: sessionId,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error("Failed to start stream");
        }
        // console.log("response_body:",response.body);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const text = decoder.decode(value, { stream: true });
          console.log(JSON.stringify(text));
          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split(/\r?\n\r?\n/);
          // console.log("Parts:", parts);
          buffer = parts.pop() ?? "";
          console.log("Buffer:", buffer);
          for (const part of parts) {
            console.log("Processing part:", part);
            const lines = part.split(/\r?\n/);
            console.log("lines:", lines);
            const eventLine = lines.find((line) => line.startsWith("event:"));
            const dataLine = lines.find((line) => line.startsWith("data:"));
            console.log("eventLine:", eventLine, "dataLine:", dataLine);
            if (!eventLine || !dataLine) continue;

            const eventName = eventLine.replace("event:", "").trim();
            console.log("Received event:", eventName, "data:", dataLine);
            if (eventName === "character_response") {
              /* ignore streaming chunks — we'll re-fetch history once the stream finishes */
              const payload = JSON.parse(dataLine.replace("data:", "").trim());
              const assistantMessage: Message = {
                id: crypto.randomUUID(),
                sessionId,
                characterId: payload.character_id,
                role: "assistant",
                content: normalizeMarkdown(payload.response),
                createdAt: payload.created_at ? Number(payload.created_at) : Date.now(),
              };

              setLiveTurns((turns) =>
                turns.map((turn) =>
                  turn.conv_id === pendingTurnId
                    ? {
                        ...turn,
                        responses: [...turn.responses, assistantMessage],
                      }
                    : turn,
                ),
              );
            }

            if (eventName === "done") {
              setStreamingIds((ids) =>
                ids.filter((id) => id !== pendingQueryId),
              );
              // after stream completes, refresh the session history so UI shows persisted replies
              try {
                await loadSessionMessages(sessionId);
              } catch (e) {
                // ignore
              }
              break;
            }
          }
        }

        setStreamingIds((ids) => ids.filter((id) => id !== pendingQueryId));
      } catch {
        setStreamingIds((ids) => ids.filter((id) => id !== pendingQueryId));
        setLiveTurns((cur) =>
          cur.filter((turn) => turn.conv_id !== pendingTurnId),
        );
      }

      setState((s) => ({
        ...s,
        sessions: s.sessions.map((x) =>
          x.id === sessionId ? { ...x, updatedAt: Date.now() } : x,
        ),
      }));
    },
    [state.groups, state.sessions],
  );

  return {
    ...state,
    user,
    streamingIds,
    login,
    logout,
    addGroup,
    updateGroup,
    deleteGroup,
    addCharacter,
    updateCharacter,
    deleteCharacter,
    createSession,
    loadSessionMessages,
    deleteSession,
    sendMessage,
    liveTurns,
  };
}

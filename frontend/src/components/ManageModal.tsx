import { useState, useEffect } from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
// import { useToast } from "@/hooks/use-toast";
// import {Toast} from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Plus, Trash2, Users, Sparkles, Pencil, X } from 'lucide-react';
import type { Character, Group } from '@/lib/types';
import {toast} from 'sonner';

interface ManageModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groups: Group[];
  characters: Character[];
  onAddGroup: (name: string, description: string, characterIds: string[]) => void;
  onUpdateGroup: (id: string, name: string, description: string, characterIds: string[]) => Promise<{ success: boolean; error?: string;detail?: string }>;
  onDeleteGroup: (id: string) => void;
  onAddCharacter: (name: string, persona: string, color: Character['color'], traits: string[]) => Promise<Character>;
  onUpdateCharacter: (id: string, name: string, persona: string, color: Character['color'], traits: string[]) => void;
  onDeleteCharacter: (id: string) => void;
  editGroup?: Group | null;
  editCharacter?: Character | null;
  onEditConsumed?: () => void;
  scopeGroupId?: string | null;
}

const colorOptions: { value: Character['color']; label: string; class: string }[] = [
  { value: 'cyan', label: 'Sky', class: 'bg-sky-500' },
  { value: 'green', label: 'Teal', class: 'bg-teal-500' },
  { value: 'pink', label: 'Rose', class: 'bg-rose-500' },
  { value: 'purple', label: 'Violet', class: 'bg-violet-500' },
  { value: 'blue', label: 'Blue', class: 'bg-blue-500' },
  { value: 'yellow', label: 'Amber', class: 'bg-amber-500' },
];

const colorText: Record<string, string> = {
  cyan: 'text-sky-400',
  green: 'text-teal-400',
  pink: 'text-rose-400',
  purple: 'text-violet-400',
  blue: 'text-blue-400',
  yellow: 'text-amber-400',
};

export function ManageModal({
  open,
  onOpenChange,
  groups,
  characters,
  onAddGroup,
  onUpdateGroup,
  onDeleteGroup,
  onAddCharacter,
  onUpdateCharacter,
  onDeleteCharacter,
  editGroup,
  editCharacter,
  onEditConsumed,
  scopeGroupId
}: ManageModalProps) {
  const [tab, setTab] = useState<'groups' | 'characters'>('groups');

  // group form
  const [gName, setGName] = useState('');
  const [gDesc, setGDesc] = useState('');
  const [gChars, setGChars] = useState<string[]>([]);
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null);

  // character form
  const [cName, setCName] = useState('');
  const [cPersona, setCPersona] = useState('');
  const [cColor, setCColor] = useState<Character['color']>('cyan');
  const [cTraits, setCTraits] = useState<string[]>([]);
  const [cTraitInput, setCTraitInput] = useState('');
  const [editingCharId, setEditingCharId] = useState<string | null>(null);

  const scopedGroup = scopeGroupId ? groups.find((g) => g.id === scopeGroupId) ?? null : null;
  const isScoped = !!scopedGroup;
  const scopedCharacterIds = scopedGroup?.characterIds ?? [];
  const scopedCharacters = isScoped
    ? characters.filter((c) => scopedCharacterIds.includes(c.id))
    : characters;
  const visibleGroups = isScoped
  ? scopedGroup
    ? [scopedGroup]
    : []
  : groups;

  const visibleCharacters = scopedCharacters;
  useEffect(() => {
    if (!open) {
      resetGroupForm();
      resetCharForm();
    }
  }, [open]);

  useEffect(() => {
    if (editGroup && open) {
      setTab('groups');
      startEditGroup(editGroup);
      onEditConsumed?.();
    }
  }, [editGroup, open]);

  useEffect(() => {
    if (editCharacter && open) {
      setTab('characters');
      startEditCharacter(editCharacter);
      onEditConsumed?.();
    }
  }, [editCharacter, open]);

  useEffect(() => {
    if (
      open &&
      isScoped &&
      scopedGroup &&
      !editingGroupId
    ) {
      startEditGroup(scopedGroup);
    }
}, [open, isScoped, scopedGroup]);

  const resetGroupForm = () => {
    setGName('');
    setGDesc('');
    setGChars([]);
    setEditingGroupId(null);
  };

  const resetCharForm = () => {
    setCName('');
    setCPersona('');
    setCColor('cyan');
    setCTraits([]);
    setCTraitInput('');
    setEditingCharId(null);
  };

  const toggleChar = (id: string) => {
    setGChars((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const startEditGroup = (g: Group) => {
    setEditingGroupId(g.id);
    setGName(g.name);
    setGDesc(g.description);
    setGChars([...g.characterIds]);
  };

  const submitGroup = async () => {
    if (!gName.trim() || !gDesc.trim()){
      
        toast.error('Group name and description are required', { description: 'Please fill in both fields before submitting.' });
        return; // ← keep form open so user can retry
      }
    if(gChars.length>5){
        toast.error("Characters count",{ description: 'Please select do not select more than 5 characters in a group.' })
        return;
    }
    if (editingGroupId) {
       const result = await onUpdateGroup(editingGroupId, gName.trim(), gDesc.trim(), gChars);
       if (!result.success) {
          toast.error(result.error ?? "Failed");
          return;
       }
    } else {
      onAddGroup(gName.trim(), gDesc.trim(), gChars);
    }
    resetGroupForm();
  };

  const addTrait = () => {
    const t = cTraitInput.trim();
    if (t && !cTraits.includes(t)) {
      setCTraits([...cTraits, t]);
    }
    setCTraitInput('');
  };

  const removeTrait = (t: string) => {
    setCTraits(cTraits.filter((x) => x !== t));
  };

  const startEditCharacter = (c: Character) => {
    setEditingCharId(c.id);
    setCName(c.name);
    setCPersona(c.persona);
    setCColor(c.color);
    setCTraits([...(c.traits ?? [])]);
    setCTraitInput('');
  };

 const submitCharacter = async () => {
  if (!cName.trim() || !cPersona.trim()) return;
  
  if (editingCharId) {
    if (scopedGroup?.grpType === "seed") {
       toast.error("Cannot edit characters in seed group",{ description: 'You cannot edit characters in a seed group.' })
    }
    onUpdateCharacter(
      editingCharId,
      cName.trim(),
      cPersona.trim(),
      cColor,
      cTraits
    );
  } else {
    if (scopedGroup?.grpType==="seed"){
      toast.error("Cannot add character to seed group",{ description: 'You cannot add characters to a seed group.' })
      return;
    }
    const newChar = await onAddCharacter(
      cName.trim(),
      cPersona.trim(),
      cColor,
      cTraits
    );

    if (isScoped && scopedGroup) {
      await onUpdateGroup(
        scopedGroup.id,
        scopedGroup.name,
        scopedGroup.description,
        [...new Set([...scopedGroup.characterIds, newChar.id])]
      );
    }
  }

  resetCharForm();
  onOpenChange(false); // Close the modal after submission
};

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <span className="hidden" />
      </DialogTrigger>
      <DialogContent className="glass max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
              {isScoped
                  ? `Manage ${scopedGroup?.name}`
                  : "Manage groups & characters"}
          </DialogTitle>
        </DialogHeader>

        <div className="flex gap-2 border-b border-border pb-3">
          <button
            onClick={() => setTab('groups')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === 'groups' ? 'bg-primary/15 text-primary border border-primary/30' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Users className="h-4 w-4" /> Groups
          </button>
          <button
            onClick={() => setTab('characters')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === 'characters' ? 'bg-accent/15 text-accent border border-accent/30' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Sparkles className="h-4 w-4" /> Characters
          </button>
        </div>

        <div className="overflow-y-auto scrollbar-neon pr-1 flex-1">
          {tab === 'groups' ? (
            <div className="space-y-6">
              {/* Existing groups */}
              <div className="space-y-2">
                {visibleGroups.length === 0 && <p className="text-sm text-muted-foreground">No groups yet.</p>}
               {(isScoped ? [scopedGroup!] : groups).map((g) => (
                  <div key={g.id} className="glass rounded-lg p-3 flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium text-sm">{g.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{g.description || 'No description'}</p>
                      <div className="flex -space-x-2 mt-2">
                        {g.characterIds.map((id) => {
                          const c = characters.find((x) => x.id === id);
                          if (!c) return null;
                          return (
                            <Avatar
                                key={id}
                                className="h-6 w-6 ring-2 ring-background cursor-pointer hover:scale-110 transition-transform"
                                onClick={() => {
                                  setTab("characters");
                                  startEditCharacter(c);
                                }}
                            >
                              <AvatarImage src={c.avatar} />
                              <AvatarFallback className={`text-[9px] ${colorText[c.color]} bg-background`}>
                                {c.name.slice(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar> 
                          );
                        })}
                      </div>
                    </div>
                    
                      {!isScoped && g.grpType !== "seed" && (
              <div className="flex gap-1 shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => startEditGroup(g)}
                  title="Edit group"
                >
                  <Pencil className="h-4 w-4 text-muted-foreground" />
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDeleteGroup(g.id)}
                  title="Delete group"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            )}
                  </div>
                ))}
              </div>

              {/* New / edit group form */}
              {(!isScoped || editingGroupId) && (scopedGroup?.grpType!=="seed") && (
              <div className="glass rounded-lg p-4 space-y-3 border border-primary/30">
                <h3 className="text-sm font-semibold text-primary">
                    {editingGroupId
                      ? "Edit group"
                      : isScoped
                        ? "Group details"
                        : "Create new group"}
                </h3>
                <div className="space-y-1.5">
                  <Label htmlFor="g-name">Name</Label>
                  <Input id="g-name" value={gName} onChange={(e) => setGName(e.target.value)} placeholder="Group name" className="bg-background/50" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="g-desc">Description</Label>
                  <Textarea id="g-desc" value={gDesc} onChange={(e) => setGDesc(e.target.value)} placeholder="What is this group about?" rows={2} className="bg-background/50 resize-none" />
                </div>
                <div className="space-y-1.5">
                  <Label>Members ({gChars.length} selected)</Label>
                  <div className="flex flex-wrap gap-2">
                    {scopedCharacters.map((c) => {
                      const selected = gChars.includes(c.id);
                      return (
                        <button
                          key={c.id}
                          onClick={() => toggleChar(c.id)}
                          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs border transition-all ${
                            selected
                              ? `${colorText[c.color]} border-current bg-current/10`
                              : 'text-muted-foreground border-border hover:border-foreground/30'
                          }`}
                        >
                          <Avatar className="h-5 w-5">
                            <AvatarImage src={c.avatar} />
                            <AvatarFallback className={`text-[8px] ${colorText[c.color]} bg-background`}>
                              {c.name.slice(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          {c.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={submitGroup} className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground">
                    <Plus className="h-4 w-4 mr-1" /> {editingGroupId ? 'Save changes' : 'Create group'}
                  </Button>
                  {editingGroupId && (
                    <Button variant="outline" onClick={resetGroupForm} className="px-4">
                      Cancel
                    </Button>
                  )}
                </div>
              </div>)}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Existing characters */}
              <div className="space-y-2">
                {scopedCharacters.length === 0 && <p className="text-sm text-muted-foreground">No characters yet.</p>}
                {scopedCharacters.map((c) => (
                  <div key={c.id} className="glass rounded-lg p-3 flex items-center gap-3">
                    <Avatar className={`h-10 w-10 ring-2 ring-${c.color}-400/40`}>
                      <AvatarImage src={c.avatar} />
                      <AvatarFallback className={`text-xs ${colorText[c.color]} bg-background`}>
                        {c.name.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium ${colorText[c.color]}`}>{c.name}</p>
                      <p className="text-xs text-muted-foreground truncate">{c.persona || 'No persona'}</p>
                      {c.traits && c.traits.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {c.traits.map((t) => (
                            <Badge key={t} variant="secondary" className="text-[10px] px-1.5 py-0">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    {c.type !== "seed" && (
                      <div className="flex gap-1 shrink-0">
                      <Button variant="ghost" size="icon" onClick={() => startEditCharacter(c)} title="Edit character">
                        <Pencil className="h-4 w-4 text-muted-foreground" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => onDeleteCharacter(c.id)} title="Delete character">
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>)
                    }
                  </div>
                ))}
              </div>

              {/* New / edit character form */}
              {(scopedGroup?.grpType!=="seed") && (
                <div className="glass rounded-lg p-4 space-y-3 border border-accent/30">
                  <h3 className="text-sm font-semibold text-accent">
                    {editingCharId ? 'Edit character' : 'Create new character'}
                  </h3>
                  <div className="space-y-1.5">
                    <Label htmlFor="c-name">Name</Label>
                  <Input id="c-name" value={cName} onChange={(e) => setCName(e.target.value)} placeholder="Character name" className="bg-background/50" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c-persona">Persona</Label>
                  <Textarea id="c-persona" value={cPersona} onChange={(e) => setCPersona(e.target.value)} placeholder="Describe this character's personality..." rows={3} className="bg-background/50 resize-none" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c-traits">Traits</Label>
                  <div className="flex gap-2">
                    <Input
                      id="c-traits"
                      value={cTraitInput}
                      onChange={(e) => setCTraitInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addTrait();
                        }
                      }}
                      placeholder="Add a trait and press Enter..."
                      className="bg-background/50"
                    />
                    <Button variant="outline" size="icon" onClick={addTrait} className="shrink-0">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {cTraits.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {cTraits.map((t) => (
                        <Badge key={t} variant="secondary" className="gap-1 pr-1">
                          {t}
                          <button onClick={() => removeTrait(t)} className="hover:text-destructive">
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label>Accent color</Label>
                  <div className="flex gap-2">
                    {colorOptions.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setCColor(opt.value)}
                        className={`h-8 w-8 rounded-full ${opt.class} transition-all ${
                          cColor === opt.value ? 'ring-2 ring-offset-2 ring-offset-background ring-white scale-110' : 'opacity-60 hover:opacity-100'
                        }`}
                        title={opt.label}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={submitCharacter} className="flex-1 bg-accent hover:bg-accent/90 text-accent-foreground">
                    <Plus className="h-4 w-4 mr-1" /> {editingCharId ? 'Save changes' : 'Create character'}
                  </Button>
                  {editingCharId && (
                    <Button variant="outline" onClick={resetCharForm} className="px-4">
                      Cancel
                    </Button>
                  )}
                </div>
              </div>)}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

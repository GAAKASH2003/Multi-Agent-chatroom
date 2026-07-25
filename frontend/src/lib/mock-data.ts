import type { Character, Group, ChatSession, Message } from './types';

export const seedCharacters: Character[] = [
  // {
  //   id: 'c1',
  //   name: 'Nova',
  //   avatar: 'https://images.pexels.com/photos/7338560/pexels-photo-7338560.jpeg?auto=compress&cs=tinysrgb&w=200',
  //   persona: 'A curious AI researcher who loves discussing technology and the future.',
  //   color: 'cyan',
  // },
  // {
  //   id: 'c2',
  //   name: 'Ember',
  //   avatar: 'https://images.pexels.com/photos/7338560/pexels-photo-7338560.jpeg?auto=compress&cs=tinysrgb&w=200',
  //   persona: 'A fiery creative writer with a passion for storytelling.',
  //   color: 'pink',
  // },
  // {
  //   id: 'c3',
  //   name: 'Sage',
  //   avatar: 'https://images.pexels.com/photos/7338560/pexels-photo-7338560.jpeg?auto=compress&cs=tinysrgb&w=200',
  //   persona: 'A calm philosopher who ponders the deep questions of life.',
  //   color: 'green',
  // },
  // {
  //   id: 'c4',
  //   name: 'Volt',
  //   avatar: 'https://images.pexels.com/photos/7338560/pexels-photo-7338560.jpeg?auto=compress&cs=tinysrgb&w=200',
  //   persona: 'An energetic engineer who solves problems at lightning speed.',
  //   color: 'purple',
  // },
];

export const seedGroups: Group[] = [
  // {
  //   id: 'g1',
  //   name: 'Tech Think Tank',
  //   description: 'A group of AI minds discussing technology and innovation.',
  //   characterIds: ['c1', 'c4'],
  //   createdAt: Date.now() - 86400000,
  // },
  // {
  //   id: 'g2',
  //   name: 'Creative Circle',
  //   description: 'Writers and philosophers exploring ideas together.',
  //   characterIds: ['c2', 'c3'],
  //   createdAt: Date.now() - 43200000,
  // },
];

export const seedSessions: ChatSession[] = [
  // {
  //   id: 's1',
  //   groupId: 'g1',
  //   title: 'Future of AI',
  //   createdAt: Date.now() - 3600000,
  //   updatedAt: Date.now() - 600000,
  // },
  // {
  //   id: 's2',
  //   groupId: 'g2',
  //   title: 'The art of storytelling',
  //   createdAt: Date.now() - 7200000,
  //   updatedAt: Date.now() - 1200000,
  // },
];

export const seedMessages: Message[] = [
  // {
  //   id: 'm1',
  //   sessionId: 's1',
  //   characterId: null,
  //   role: 'user',
  //   content: 'What do you think the future of AI holds?',
  //   createdAt: Date.now() - 3600000,
  // },
  // {
  //   id: 'm2',
  //   sessionId: 's1',
  //   characterId: 'c1',
  //   role: 'assistant',
  //   content: 'I believe AI will become deeply integrated into every aspect of our lives, augmenting human creativity rather than replacing it.',
  //   createdAt: Date.now() - 3599000,
  // },
  // {
  //   id: 'm3',
  //   sessionId: 's1',
  //   characterId: 'c4',
  //   role: 'assistant',
  //   content: 'Agreed! The real breakthrough will be in how fast we can iterate on ideas with AI as a collaborator.',
  //   createdAt: Date.now() - 3598000,
  // },
  // {
  //   id: 'm4',
  //   sessionId: 's2',
  //   characterId: null,
  //   role: 'user',
  //   content: 'What makes a great story?',
  //   createdAt: Date.now() - 7200000,
  // },
  // {
  //   id: 'm5',
  //   sessionId: 's2',
  //   characterId: 'c2',
  //   role: 'assistant',
  //   content: 'A great story lives in the tension between what is and what could be. It breathes through conflict and resolution.',
  //   createdAt: Date.now() - 7199000,
  // },
];

const characterReplies: Record<string, string[]> = {
  // c1: [
  //   'That is a fascinating angle. From a technical lens, it comes down to how systems learn to generalize.',
  //   'I would add that the data we feed these systems shapes the reality they perceive.',
  //   'Precisely. The architecture matters, but the intent behind it matters more.',
  // ],
  // c2: [
  //   'Ooh, I love where this is going. Picture a scene where the protagonist faces exactly that dilemma.',
  //   'Stories are mirrors, you know? They show us who we are when no one is watching.',
  //   'The best twists are the ones the reader swears they saw coming.',
  // ],
  // c3: [
  //   'One must consider the ethical weight of such a choice. What does it say about our values?',
  //   'Stillness often reveals more than motion. Sit with the question a moment.',
  //   'Truth is rarely simple. It wears many faces depending on who looks.',
  // ],
  // c4: [
  //   'Quick take: we can prototype that in an afternoon if we break it into the right pieces.',
  //   'Speed is a feature. Ship the smallest version, learn, iterate.',
  //   'I would optimize the bottleneck first — everything else is noise until then.',
  // ],
};

export function generateReply(characterId: string, userMessage: string): string {
  const replies = characterReplies[characterId] || characterReplies.c1;
  const idx = Math.floor((userMessage.length + Date.now()) % replies.length);
  return replies[idx];
}

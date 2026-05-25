import type { Spot, SpotCategory, SpotTag } from "@/types/spot";
import { SEED_SPOTS } from "@/lib/seed-data";

const STORAGE_KEY = "multi-mapping:spots:v1";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readUserSpots(): Spot[] {
  if (!isBrowser()) return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Spot[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeUserSpots(spots: Spot[]): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(spots));
  } catch (err) {
    console.error("Failed to write to localStorage:", err);
  }
}

export function loadAllSpots(): Spot[] {
  const userSpots = readUserSpots();
  return [...userSpots, ...SEED_SPOTS];
}

export function loadSpotById(id: string): Spot | null {
  return loadAllSpots().find((s) => s.id === id) ?? null;
}

export interface NewSpotInput {
  name: string;
  description: string;
  category: SpotCategory;
  latitude: number;
  longitude: number;
  nickname: string;
  tags: SpotTag[];
}

export function createSpot(input: NewSpotInput): Spot {
  const now = new Date().toISOString();
  const newSpot: Spot = {
    id: typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: input.name,
    description: input.description || null,
    category: input.category,
    latitude: input.latitude,
    longitude: input.longitude,
    nickname: input.nickname || null,
    created_at: now,
    updated_at: now,
    tags: input.tags,
  };
  const userSpots = readUserSpots();
  writeUserSpots([newSpot, ...userSpots]);
  return newSpot;
}

export function deleteSpot(id: string): boolean {
  const userSpots = readUserSpots();
  const next = userSpots.filter((s) => s.id !== id);
  if (next.length === userSpots.length) return false;
  writeUserSpots(next);
  return true;
}

export function isUserCreatedSpot(id: string): boolean {
  return readUserSpots().some((s) => s.id === id);
}

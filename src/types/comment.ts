export interface Comment {
  id: string;
  spot_id: string;
  body: string;
  nickname: string | null;
  created_at: string;
}

export interface CommentCreatePayload {
  body: string;
  nickname?: string;
  turnstileToken: string;
}

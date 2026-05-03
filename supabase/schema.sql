-- XYRA — Supabase schema
-- Run this in the Supabase SQL Editor before launching the app.

-- ── Profiles table ────────────────────────────────────────────────────────────
create table if not exists public.profiles (
  id          uuid        references auth.users(id) on delete cascade primary key,
  store_name  text        not null default '',
  store_type  text        not null default 'Grocery',
  pincode     text        not null default '600001',
  categories  text[]      not null default '{}',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- ── Row Level Security ────────────────────────────────────────────────────────
alter table public.profiles enable row level security;

create policy "Users can read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- ── Auto-update updated_at on every row change ────────────────────────────────
create or replace function public.handle_updated_at()
returns trigger language plpgsql security definer as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace trigger profiles_updated_at
  before update on public.profiles
  for each row execute procedure public.handle_updated_at();

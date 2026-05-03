/**
 * XYRA — Supabase seed / connection test
 * Run: SUPABASE_SERVICE_KEY=<your-service-role-key> node seed.mjs
 * Prerequisites: npm install @supabase/supabase-js  (or use the already-installed version in frontend)
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://luzpbzwxwonivpobffeq.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('Set SUPABASE_SERVICE_KEY env var to your service_role secret key.');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY, {
  auth: { persistSession: false },
});

async function main() {
  console.log('Checking Supabase connection…');

  const { error } = await supabase.from('profiles').select('id').limit(1);

  if (error) {
    console.error('Connection failed:', error.message);
    console.log('\nMake sure you have:');
    console.log('  1. Run supabase/schema.sql in the Supabase SQL editor');
    console.log('  2. Passed the correct service_role key via SUPABASE_SERVICE_KEY');
    process.exit(1);
  }

  console.log('✓ Connected — profiles table is accessible.');
  console.log('\nTo seed a test user:');
  console.log('  Supabase Dashboard → Authentication → Users → Add user');
  console.log('  Then sign in with XYRA and complete onboarding — the profile row will be created automatically.');
}

main();

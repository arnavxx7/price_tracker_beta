import { createClient } from '@supabase/supabase-js'


const supabase_url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const publishable_key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

export const supabase = createClient(supabase_url as string, publishable_key as string);


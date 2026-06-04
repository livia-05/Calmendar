import os
import re
import json
import random
import hashlib
import anthropic
from server.database import get_db


# ── Local (no-API) suggestion pool ──────────────────────────────────────────

_ACTIVITY_POOL = [
    # ── Physical / Movement ──────────────────────────────────────────────────
    {
        "name": "Go for a walk",
        "description": "Head outside for a short walk — around the block or somewhere nearby.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["hiking", "walk", "outdoor", "nature", "running", "exercise"],
        "tags": ["physical", "outdoor", "screen_free"],
        "reason": "Getting outside and moving clears your head after focused work."
    },
    {
        "name": "Stretch or do yoga",
        "description": "A few gentle stretches or a short yoga flow to release tension in your body.",
        "short_mins": 5, "long_mins": 20,
        "hobby_keywords": ["yoga", "stretch", "fitness", "gym", "pilates", "exercise"],
        "tags": ["physical", "mindful", "screen_free"],
        "reason": "Stretching counteracts the tension that builds up during long periods of sitting."
    },
    {
        "name": "Quick workout",
        "description": "A few minutes of jumping jacks, push-ups, or whatever exercise you enjoy.",
        "short_mins": 5, "long_mins": 20,
        "hobby_keywords": ["gym", "fitness", "workout", "exercise", "running", "sport", "crossfit"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "Short bursts of exercise release endorphins and boost your energy almost immediately."
    },
    {
        "name": "Dance to a song",
        "description": "Put on one song you love and just dance — no one is watching.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["dance", "dancing", "music", "fitness", "exercise"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "Dancing is movement plus music — a double hit of mood improvement in under five minutes."
    },
    {
        "name": "Take a bike ride",
        "description": "Hop on your bike for a short loop around the neighborhood.",
        "short_mins": 15, "long_mins": 30,
        "hobby_keywords": ["cycling", "bike", "biking", "outdoor", "exercise", "running"],
        "tags": ["physical", "outdoor", "screen_free"],
        "reason": "Cycling gives you the mental benefits of a walk at twice the pace."
    },
    {
        "name": "Do some jumping jacks",
        "description": "Stand up and do a set of jumping jacks to get your blood moving.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["fitness", "exercise", "gym", "workout"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "Even 2 minutes of movement fights the fatigue that builds from sitting still."
    },
    {
        "name": "Neck and shoulder rolls",
        "description": "Slowly roll your neck and shoulders — forward, back, and side to side.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["yoga", "stretch", "exercise", "wellness"],
        "tags": ["physical", "mindful", "screen_free"],
        "reason": "Tension loves to hide in your neck and shoulders — rolling it out takes under five minutes."
    },
    {
        "name": "Walk around the block",
        "description": "A single loop around the block — just enough to reset your perspective.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["outdoor", "walk", "nature", "exercise"],
        "tags": ["physical", "outdoor", "screen_free"],
        "reason": "Changing your environment, even briefly, breaks a mental rut better than anything at your desk."
    },
    {
        "name": "Do some push-ups or sit-ups",
        "description": "Drop and do a set of whatever feels good — no equipment needed.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["gym", "fitness", "workout", "exercise", "sport"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "A quick set of bodyweight exercises wakes up your body and sharpens focus fast."
    },
    {
        "name": "Wall sit challenge",
        "description": "Find a wall and hold a wall sit for as long as you can — it's harder than it looks.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["gym", "fitness", "workout", "exercise"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "A timed wall sit is a quick way to feel physically accomplished between mental tasks."
    },
    {
        "name": "Step outside for fresh air",
        "description": "Go outside, even just to your doorstep or balcony, and breathe for a minute.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["outdoor", "nature", "garden", "balcony"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Fresh air and a change of scenery is one of the simplest and most effective resets."
    },
    {
        "name": "Slow mindful walk",
        "description": "Walk slowly and notice five things you wouldn't normally pay attention to.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["hiking", "walk", "outdoor", "nature", "mindfulness", "meditation"],
        "tags": ["physical", "outdoor", "mindful", "screen_free"],
        "reason": "Mindful walking combines movement and presence — a powerful stress reset."
    },
    {
        "name": "Jump rope",
        "description": "Grab a jump rope (or just jump in place) for a few energizing minutes.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["fitness", "exercise", "gym", "sport", "workout"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "Jumping activates your whole body and sends a jolt of energy through your system."
    },
    {
        "name": "Sit in the sun",
        "description": "Find a sunny spot — inside or outside — and just sit in the warmth for a few minutes.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["outdoor", "nature", "garden", "relaxation"],
        "tags": ["outdoor", "screen_free", "mindful", "relaxing"],
        "reason": "Natural light boosts serotonin levels almost immediately and helps regulate your energy."
    },
    {
        "name": "Gentle eye exercises",
        "description": "Look at something 20 feet away for 20 seconds, then focus on something close — repeat a few times.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["wellness", "health", "exercise"],
        "tags": ["screen_free", "mindful"],
        "reason": "The 20-20-20 rule is one of the best things you can do for screen-tired eyes."
    },
    # ── Creative ─────────────────────────────────────────────────────────────
    {
        "name": "Sketch or doodle",
        "description": "Grab any pen and paper and draw whatever comes to mind — no goal, just flow.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["art", "drawing", "painting", "sketch", "illustration", "creative", "design"],
        "tags": ["creative", "screen_free", "relaxing"],
        "reason": "Unstructured drawing lets your mind wander freely, which is exactly what recharges it."
    },
    {
        "name": "Write in a journal",
        "description": "Spend a few minutes writing whatever is on your mind — thoughts, feelings, anything.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["journaling", "writing", "diary", "blogging", "journal"],
        "tags": ["reflective", "screen_free", "quiet"],
        "reason": "Getting thoughts out of your head and onto paper clears mental clutter."
    },
    {
        "name": "Write a haiku",
        "description": "Write a haiku about your day so far — 5 syllables, 7 syllables, 5 syllables.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["writing", "poetry", "creative", "journaling"],
        "tags": ["creative", "screen_free", "quiet"],
        "reason": "The constraint of a haiku forces your brain to slow down and find beauty in small things."
    },
    {
        "name": "Color or paint",
        "description": "Open a coloring book or grab watercolors and fill in a page with no pressure.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["art", "painting", "drawing", "coloring", "creative"],
        "tags": ["creative", "screen_free", "relaxing"],
        "reason": "Coloring is meditative — your hand stays busy while your mind rests."
    },
    {
        "name": "Take some photos",
        "description": "Walk around with your phone camera and photograph something interesting.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["photography", "photo", "art", "outdoor", "creative"],
        "tags": ["creative", "outdoor", "screen_free"],
        "reason": "Photography makes you look at familiar things with fresh eyes."
    },
    {
        "name": "Try hand lettering",
        "description": "Practice writing a word or phrase in a decorative style — just a pen and paper.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["art", "drawing", "calligraphy", "creative", "design", "writing"],
        "tags": ["creative", "screen_free", "quiet"],
        "reason": "Hand lettering is a slow, satisfying practice that fully occupies your hands and eyes."
    },
    {
        "name": "Write down 5 ideas",
        "description": "Pick any topic and brainstorm five ideas — the wilder, the better.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["writing", "creative", "journaling", "brainstorm"],
        "tags": ["creative", "reflective", "screen_free"],
        "reason": "Idea generation is a creative muscle — exercising it briefly keeps it sharp."
    },
    {
        "name": "Make a playlist",
        "description": "Build a playlist for your current mood — no skipping, just add what fits.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["music", "guitar", "piano", "singing", "concert"],
        "tags": ["creative", "relaxing"],
        "reason": "Curating music is a low-effort creative act that leaves you with something you can enjoy all week."
    },
    {
        "name": "Do some origami",
        "description": "Fold a piece of paper into something — a crane, a boat, or anything you look up.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["craft", "art", "creative", "drawing"],
        "tags": ["creative", "screen_free", "quiet"],
        "reason": "Origami keeps your hands moving in a precise, calming rhythm that quiets mental noise."
    },
    {
        "name": "Doodle your dream home layout",
        "description": "Sketch out a floor plan of your ideal home — any size, any style.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["art", "drawing", "architecture", "design", "creative"],
        "tags": ["creative", "screen_free", "fun"],
        "reason": "Playful imagination gives your logical brain a genuine rest."
    },
    # ── Mindful / Relaxing ───────────────────────────────────────────────────
    {
        "name": "Quick meditation",
        "description": "Sit comfortably, close your eyes, and focus on your breathing for a few minutes.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["meditation", "mindful", "mindfulness", "yoga", "calm", "zen"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "Even a brief breathing pause measurably reduces stress and sharpens focus."
    },
    {
        "name": "Box breathing",
        "description": "Breathe in for 4 counts, hold for 4, out for 4, hold for 4 — repeat 4 times.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["meditation", "mindfulness", "yoga", "calm", "wellness"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "Box breathing activates your parasympathetic nervous system and calms anxiety fast."
    },
    {
        "name": "Body scan meditation",
        "description": "Lie down and slowly bring attention to each part of your body from feet to head.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["meditation", "mindfulness", "yoga", "wellness", "calm"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "A body scan releases physical tension you didn't realize you were holding."
    },
    {
        "name": "Sit quietly without your phone",
        "description": "Put your phone face-down and just sit with your thoughts for 5 minutes.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["meditation", "mindfulness", "calm", "wellness"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "Unstructured stillness is genuinely rare — your brain will thank you for it."
    },
    {
        "name": "Stare out the window",
        "description": "Look outside, let your eyes go soft, and let your mind wander without guilt.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["outdoor", "nature", "meditation", "calm"],
        "tags": ["mindful", "screen_free", "relaxing"],
        "reason": "Unfocused attention — sometimes called 'diffuse mode' — is where insights often arrive."
    },
    {
        "name": "Listen to nature sounds",
        "description": "Put on rain, forest, or ocean sounds and let them wash over you.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["outdoor", "nature", "meditation", "calm", "music"],
        "tags": ["mindful", "screen_free", "relaxing"],
        "reason": "Natural sounds lower cortisol and shift your nervous system toward rest."
    },
    {
        "name": "Write a gratitude list",
        "description": "Write down three things you are genuinely grateful for right now.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["journaling", "mindfulness", "writing", "wellness"],
        "tags": ["reflective", "screen_free", "quiet"],
        "reason": "Gratitude practice is one of the highest-evidence interventions for improving mood."
    },
    {
        "name": "Progressive muscle relaxation",
        "description": "Tense each muscle group for 5 seconds, then release — start at your feet and work up.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["yoga", "meditation", "wellness", "mindfulness", "exercise"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "PMR teaches your body the contrast between tension and release, making it easier to let go."
    },
    {
        "name": "Do nothing for 5 minutes",
        "description": "Set a timer for 5 minutes and do absolutely nothing — just exist.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["meditation", "mindfulness", "calm", "wellness"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "Deliberate rest is not laziness — it's one of the most productive things your brain can do."
    },
    {
        "name": "Set an intention",
        "description": "Write one sentence about how you want to show up for the rest of the day.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["journaling", "mindfulness", "wellness", "meditation"],
        "tags": ["reflective", "mindful", "screen_free"],
        "reason": "A clear intention acts like a rudder — small but steering you in the right direction."
    },
    # ── Social ───────────────────────────────────────────────────────────────
    {
        "name": "Text or call a friend",
        "description": "Reach out to someone — even a quick message to check in goes a long way.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["social", "friends", "family", "people", "chat"],
        "tags": ["social", "relaxing"],
        "reason": "A quick social connection reminds you there is life outside the to-do list."
    },
    {
        "name": "Send an encouraging message",
        "description": "Think of someone who might need a pick-me-up and send them a kind word.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["social", "friends", "family", "volunteer", "community"],
        "tags": ["social", "screen_free", "quiet"],
        "reason": "Doing something kind for someone else is one of the fastest mood boosters there is."
    },
    {
        "name": "Look at old photos",
        "description": "Open your photo library and scroll through old memories that make you smile.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["photography", "social", "family", "friends"],
        "tags": ["social", "relaxing"],
        "reason": "Revisiting happy memories gives your emotional state a genuine lift."
    },
    {
        "name": "Write a letter or postcard",
        "description": "Write a short note to someone you haven't connected with in a while.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["writing", "journaling", "social", "friends", "family"],
        "tags": ["social", "creative", "screen_free"],
        "reason": "The act of writing to someone specific puts you in a warm, connected headspace."
    },
    # ── Music ────────────────────────────────────────────────────────────────
    {
        "name": "Listen to music",
        "description": "Put on a favorite album or playlist, close your eyes, and just listen.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["music", "guitar", "piano", "singing", "concert", "band"],
        "tags": ["creative", "relaxing", "screen_free"],
        "reason": "Music you enjoy is one of the fastest ways to decompress between tasks."
    },
    {
        "name": "Play an instrument",
        "description": "Pick up your instrument and noodle around — no practicing, just playing.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["guitar", "piano", "drums", "music", "instrument", "bass", "violin", "ukulele"],
        "tags": ["creative", "screen_free", "relaxing"],
        "reason": "Playing without an agenda is one of the most restorative things a musician can do."
    },
    {
        "name": "Sing along to a song",
        "description": "Pick a song you love, turn it up, and sing your heart out.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["singing", "music", "vocal", "choir", "karaoke"],
        "tags": ["creative", "energetic", "screen_free"],
        "reason": "Singing releases endorphins and physically opens up your breathing."
    },
    {
        "name": "Discover a new artist",
        "description": "Open a music app, click on a genre you like, and explore something unfamiliar.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["music", "guitar", "piano", "concert", "band", "discovering"],
        "tags": ["creative", "relaxing"],
        "reason": "New music activates the dopamine reward system in a way familiar songs no longer can."
    },
    {
        "name": "Listen to a podcast",
        "description": "Put on an episode of a podcast you enjoy — something light, funny, or curious.",
        "short_mins": 15, "long_mins": 30,
        "hobby_keywords": ["podcast", "radio", "music", "learning", "audio"],
        "tags": ["relaxing", "learning"],
        "reason": "Audio content lets your eyes rest while keeping your mind pleasantly occupied."
    },
    {
        "name": "Hum or whistle something",
        "description": "No instrument? Just hum a melody you like and see where it takes you.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["music", "singing", "guitar", "piano"],
        "tags": ["creative", "screen_free", "mindful"],
        "reason": "Humming activates your vagus nerve, which directly triggers a calming response."
    },
    # ── Kitchen / Food ───────────────────────────────────────────────────────
    {
        "name": "Make tea or a snack",
        "description": "Step away from your screen, go to the kitchen, and make something to enjoy.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["cooking", "baking", "food", "coffee", "tea", "kitchen"],
        "tags": ["screen_free", "relaxing"],
        "reason": "A small ritual like making food gives you a satisfying, natural scene change."
    },
    {
        "name": "Make a smoothie",
        "description": "Throw some fruit, yogurt, or whatever you have into a blender.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["cooking", "food", "health", "fitness", "nutrition"],
        "tags": ["screen_free", "relaxing"],
        "reason": "Making something to eat or drink gives your break a satisfying, tangible end result."
    },
    {
        "name": "Brew coffee slowly",
        "description": "Make your next cup using a slow method — pour-over, French press, or Aeropress — and be present.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["coffee", "tea", "kitchen", "cooking", "barista"],
        "tags": ["screen_free", "mindful", "relaxing"],
        "reason": "Slow brewing turns a daily ritual into a mindful practice — deliberate and calming."
    },
    {
        "name": "Eat without your screen",
        "description": "If it's snack time, eat it at a table with no phone, no screen — just the food.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["food", "cooking", "mindfulness", "wellness"],
        "tags": ["screen_free", "mindful", "relaxing"],
        "reason": "Mindful eating is rarer and more restorative than it sounds."
    },
    {
        "name": "Try a new snack recipe",
        "description": "Find a simple 3-ingredient recipe and make it right now.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["cooking", "baking", "food", "kitchen", "nutrition"],
        "tags": ["creative", "screen_free"],
        "reason": "A tiny cooking project redirects your hands and gives you an immediate reward."
    },
    # ── Learning / Mind ──────────────────────────────────────────────────────
    {
        "name": "Read a few pages",
        "description": "Pick up your book and read a few pages — no pressure to finish anything.",
        "short_mins": 10, "long_mins": 30,
        "hobby_keywords": ["reading", "books", "novel", "literature", "fiction"],
        "tags": ["quiet", "screen_free", "relaxing"],
        "reason": "Reading gives your analytical mind a rest while keeping you pleasantly engaged."
    },
    {
        "name": "Learn 5 words in a new language",
        "description": "Open a language app or just look up 5 words in a language you're curious about.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["language", "learning", "travel", "culture", "books"],
        "tags": ["learning", "quiet"],
        "reason": "Learning something tiny but concrete gives your brain a satisfying win."
    },
    {
        "name": "Go down a Wikipedia rabbit hole",
        "description": "Open Wikipedia on any topic and follow links wherever your curiosity leads.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["reading", "learning", "books", "history", "science"],
        "tags": ["learning", "relaxing"],
        "reason": "Curiosity-driven reading is intrinsically motivated — and way more fun than task-driven reading."
    },
    {
        "name": "Watch a TED talk",
        "description": "Pick a TED talk on a topic you know nothing about and watch the whole thing.",
        "short_mins": 15, "long_mins": 20,
        "hobby_keywords": ["learning", "science", "technology", "books", "knowledge"],
        "tags": ["learning", "relaxing"],
        "reason": "A single TED talk can shift how you think about something for the rest of the day."
    },
    {
        "name": "Do a crossword or word puzzle",
        "description": "Pull up a crossword or word search and work through a few clues.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["puzzles", "games", "reading", "learning", "words"],
        "tags": ["learning", "quiet", "screen_free"],
        "reason": "Word puzzles engage a different part of your brain than most work does."
    },
    {
        "name": "Do a sudoku",
        "description": "Open a sudoku puzzle (app or paper) and work through it at your own pace.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["puzzles", "games", "math", "logic"],
        "tags": ["learning", "quiet"],
        "reason": "Sudoku is pattern recognition and logic — a satisfying mental switch from verbal tasks."
    },
    {
        "name": "Read some poetry",
        "description": "Look up a poet you like (or one you've never heard of) and read a few of their poems.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["reading", "writing", "poetry", "literature", "creative"],
        "tags": ["quiet", "screen_free", "relaxing"],
        "reason": "Poetry demands slow attention — it's the opposite of how we read everything else."
    },
    {
        "name": "Learn a magic trick",
        "description": "Look up a beginner card trick or coin trick and practice it until you can do it.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["magic", "tricks", "games", "creative", "performance"],
        "tags": ["creative", "screen_free", "fun"],
        "reason": "Learning something performative gives you a sense of playful accomplishment."
    },
    {
        "name": "Read about something completely unfamiliar",
        "description": "Pick a field you know nothing about — geology, beekeeping, medieval history — and read one article.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["learning", "reading", "books", "science", "history"],
        "tags": ["learning", "quiet"],
        "reason": "Deliberately seeking unfamiliar knowledge is one of the best ways to stay curious."
    },
    {
        "name": "Play a quick chess game",
        "description": "Open Chess.com or Lichess and play a 5-minute blitz game.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["chess", "games", "strategy", "puzzles", "logic"],
        "tags": ["learning", "fun"],
        "reason": "Chess is intense concentration on something completely separate from your work."
    },
    # ── Outdoor / Nature ─────────────────────────────────────────────────────
    {
        "name": "Water your plants",
        "description": "Give your plants some attention — check the soil, water them, and say hello.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["gardening", "plants", "garden", "nature", "outdoor"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Caring for plants is grounding in the most literal sense — it connects you to slow, living things."
    },
    {
        "name": "Watch birds or clouds",
        "description": "Find a window or go outside and just observe — birds, clouds, trees moving in wind.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["nature", "outdoor", "birds", "garden", "hiking"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Passive observation of nature is restorative in a way screens fundamentally aren't."
    },
    {
        "name": "Tend to a garden or plants",
        "description": "Prune, repot, or just rearrange your plants — give them a little love.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["gardening", "plants", "garden", "nature", "outdoor"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Gardening is a hands-on activity that keeps your mind present and your body moving."
    },
    {
        "name": "Collect rocks or leaves",
        "description": "Take a slow walk and pick up anything that catches your eye.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["hiking", "outdoor", "nature", "walk", "garden"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Foraging for natural objects makes you genuinely present — each step is a mini discovery."
    },
    {
        "name": "Sit in a park",
        "description": "Walk to the nearest patch of green and sit on a bench without an agenda.",
        "short_mins": 15, "long_mins": 30,
        "hobby_keywords": ["outdoor", "nature", "walk", "hiking", "garden"],
        "tags": ["outdoor", "screen_free", "mindful", "relaxing"],
        "reason": "Even a brief park visit measurably reduces stress hormones."
    },
    # ── Entertainment / Leisure ──────────────────────────────────────────────
    {
        "name": "Watch something short",
        "description": "Pull up a short video or an episode of something you enjoy and fully relax.",
        "short_mins": 15, "long_mins": 30,
        "hobby_keywords": ["tv", "movies", "netflix", "youtube", "film", "anime", "shows"],
        "tags": ["screen", "entertaining", "relaxing"],
        "reason": "Passive entertainment lets your brain rest without demanding more from you."
    },
    {
        "name": "Watch funny videos",
        "description": "Give yourself permission to go down a funny video rabbit hole for a few minutes.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["youtube", "comedy", "tv", "humor", "social media"],
        "tags": ["screen", "fun", "relaxing"],
        "reason": "Laughter literally reduces tension and is one of the quickest emotional resets."
    },
    {
        "name": "Play a mobile game",
        "description": "Open a casual game you enjoy and play without guilt for a few minutes.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["gaming", "games", "mobile games", "puzzle"],
        "tags": ["screen", "fun", "relaxing"],
        "reason": "Low-stakes games give your brain a genuine diversion from work mode."
    },
    {
        "name": "Read a comic or graphic novel",
        "description": "Grab a comic book or graphic novel and read a chapter.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["reading", "comics", "anime", "manga", "books", "art"],
        "tags": ["quiet", "relaxing", "creative"],
        "reason": "Comics engage your visual and narrative brain simultaneously — a different kind of reading."
    },
    {
        "name": "Browse a subreddit you enjoy",
        "description": "Pick a subreddit you find genuinely fun or interesting and scroll for a bit.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["reddit", "social media", "gaming", "reading", "community"],
        "tags": ["screen", "fun", "relaxing"],
        "reason": "Intentional casual browsing — with a timer — is a totally legitimate mental break."
    },
    # ── Self-care ────────────────────────────────────────────────────────────
    {
        "name": "Do a quick skincare routine",
        "description": "Wash your face, apply moisturizer, or whatever makes you feel refreshed.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["skincare", "beauty", "self-care", "wellness", "health"],
        "tags": ["screen_free", "self-care", "relaxing"],
        "reason": "A quick self-care routine is a concrete way to say 'I matter' in the middle of a busy day."
    },
    {
        "name": "Give yourself a hand massage",
        "description": "Use some lotion and slowly massage your hands and fingers — they work hard.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["wellness", "self-care", "health", "yoga"],
        "tags": ["screen_free", "self-care", "mindful"],
        "reason": "Your hands carry a lot of tension from typing — a short massage makes a surprising difference."
    },
    {
        "name": "Apply a face mask",
        "description": "Put on a sheet mask or clay mask and sit quietly until it's done.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["skincare", "self-care", "beauty", "wellness"],
        "tags": ["screen_free", "self-care", "relaxing"],
        "reason": "A face mask forces you to sit still and wait — a built-in mindful pause."
    },
    {
        "name": "Take a quick shower",
        "description": "A short warm or cool shower can reset your entire mood.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["wellness", "self-care", "health", "fitness"],
        "tags": ["screen_free", "self-care", "refreshing"],
        "reason": "Water is genuinely restorative — a shower is a full sensory reset."
    },
    {
        "name": "Drink a full glass of water",
        "description": "Get up, fill a large glass of water, and drink it slowly.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["health", "wellness", "fitness", "exercise"],
        "tags": ["screen_free", "self-care"],
        "reason": "Mild dehydration is one of the most common and underrated causes of fatigue and poor focus."
    },
    {
        "name": "Change into comfy clothes",
        "description": "If you've been in work clothes, swap to something cozy for the rest of the day.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["self-care", "wellness", "home", "comfort"],
        "tags": ["screen_free", "self-care", "relaxing"],
        "reason": "Physical comfort is directly linked to mental ease — small changes matter."
    },
    # ── Crafts / Hands-on ────────────────────────────────────────────────────
    {
        "name": "Knit or crochet",
        "description": "Pick up your current project and work a few rows without any pressure to finish.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["knitting", "crochet", "craft", "sewing", "textile", "fiber"],
        "tags": ["creative", "screen_free", "relaxing"],
        "reason": "The repetitive motion of knitting or crochet is genuinely meditative."
    },
    {
        "name": "Do a few puzzle pieces",
        "description": "Work on a jigsaw puzzle for a few minutes — no pressure to make progress.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["puzzles", "games", "craft"],
        "tags": ["screen_free", "relaxing", "quiet"],
        "reason": "Puzzle-solving is a low-stakes win that's satisfying in a completely different way from work."
    },
    {
        "name": "Build something with LEGO",
        "description": "Grab a LEGO set (or just loose bricks) and build freely for a bit.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["lego", "building", "craft", "creative", "toys"],
        "tags": ["creative", "screen_free", "fun"],
        "reason": "Free building engages spatial reasoning and creativity without any pressure to perform."
    },
    {
        "name": "Tidy one small area",
        "description": "Pick one drawer, shelf, or corner and spend a few minutes making it nicer.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["organizing", "home", "cleaning", "declutter"],
        "tags": ["screen_free", "physical", "satisfying"],
        "reason": "A tidy environment reduces background mental noise — and tidying is visible, concrete progress."
    },
    {
        "name": "Rearrange your desk",
        "description": "Clear your workspace and put things back in a way that feels better.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["organizing", "home", "design", "office"],
        "tags": ["screen_free", "physical", "satisfying"],
        "reason": "Rearranging your immediate environment can shift your mental state more than expected."
    },
    {
        "name": "Sew or embroider",
        "description": "Work a few stitches on a current project — or start something tiny and new.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["sewing", "embroidery", "craft", "fiber", "textile", "knitting"],
        "tags": ["creative", "screen_free", "quiet"],
        "reason": "Needlework keeps your hands busy in a slow, focused rhythm that calms racing thoughts."
    },
    # ── Imagination / Reflection ─────────────────────────────────────────────
    {
        "name": "Daydream about your ideal vacation",
        "description": "Close your eyes and spend a few minutes imagining a trip you'd love to take.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["travel", "outdoor", "nature", "adventure", "culture"],
        "tags": ["mindful", "screen_free", "fun"],
        "reason": "Positive mental imagery activates the same reward circuits as actually experiencing something good."
    },
    {
        "name": "Make a 3-month bucket list",
        "description": "Write down 5–10 things you want to do in the next three months — big and small.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["journaling", "writing", "travel", "planning", "goals"],
        "tags": ["reflective", "screen_free", "fun"],
        "reason": "Having things to look forward to improves your mood in the present, not just the future."
    },
    {
        "name": "Write your dream day",
        "description": "Describe your perfect day from the moment you wake up to when you go to sleep.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["journaling", "writing", "creative", "planning"],
        "tags": ["reflective", "creative", "screen_free"],
        "reason": "Articulating what you want is the first step toward actually getting it."
    },
    {
        "name": "Think of 5 things that made you smile this week",
        "description": "Sit quietly and recall five genuine moments from the past week that were good.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["mindfulness", "journaling", "wellness", "meditation"],
        "tags": ["reflective", "screen_free", "mindful"],
        "reason": "Actively recalling positive memories boosts your mood through deliberate attention, not luck."
    },
    {
        "name": "Plan your next meal out",
        "description": "Look up a restaurant you've wanted to try and plan when you might go.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["food", "cooking", "travel", "social", "dining"],
        "tags": ["fun", "relaxing"],
        "reason": "Anticipating something enjoyable is a real source of happiness — the planning itself counts."
    },
    {
        "name": "Pitch a movie to yourself",
        "description": "Invent a movie plot — genre, characters, twist — and narrate it in your head.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["movies", "writing", "creative", "storytelling", "film"],
        "tags": ["creative", "screen_free", "fun"],
        "reason": "Spontaneous storytelling is pure imagination — your analytical brain gets to clock out."
    },
    # ── Miscellaneous ────────────────────────────────────────────────────────
    {
        "name": "Watch a cooking video",
        "description": "Put on a satisfying cooking video — it's oddly relaxing even if you never make the dish.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["cooking", "food", "baking", "youtube", "tv"],
        "tags": ["screen", "relaxing"],
        "reason": "Watching someone cook is visually soothing in a way that most screen content isn't."
    },
    {
        "name": "Update your desktop wallpaper",
        "description": "Find an image that inspires you right now and set it as your background.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["art", "photography", "design", "creative"],
        "tags": ["creative", "fun"],
        "reason": "A fresh visual environment — even digital — subtly shifts your mood each time you look at it."
    },
    {
        "name": "Look up something you've always wondered about",
        "description": "Pick a question that's lived in the back of your mind and finally look it up.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["learning", "reading", "science", "books", "curiosity"],
        "tags": ["learning", "fun"],
        "reason": "Scratching a genuine curiosity itch is one of the most satisfying things a brain can do."
    },
    {
        "name": "Mini dance party",
        "description": "Put on one high-energy song and dance like nobody's watching — because nobody is.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["dance", "dancing", "music", "fitness", "exercise", "fun"],
        "tags": ["physical", "energetic", "screen_free", "fun"],
        "reason": "One song is enough to release endorphins, loosen tension, and genuinely improve your mood."
    },
    {
        "name": "Do a gratitude jar entry",
        "description": "Write one thing you're grateful for on a slip of paper and put it somewhere you'll see it.",
        "short_mins": 5, "long_mins": 5,
        "hobby_keywords": ["journaling", "mindfulness", "wellness", "gratitude"],
        "tags": ["reflective", "screen_free", "quiet"],
        "reason": "A physical gratitude practice is more memorable than a digital one — the act of writing matters."
    },
    {
        "name": "Try a new hobby for 10 minutes",
        "description": "Pick something you've been curious about and spend 10 minutes giving it a real try.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["creative", "learning", "crafts", "art", "music", "sport"],
        "tags": ["creative", "screen_free", "fun"],
        "reason": "The activation energy for new hobbies is the hardest part — starting is the whole battle."
    },
    {
        "name": "Reorganize your music library",
        "description": "Go through your saved songs or playlists and clean them up a little.",
        "short_mins": 10, "long_mins": 15,
        "hobby_keywords": ["music", "guitar", "piano", "concert", "band", "singing"],
        "tags": ["creative", "relaxing"],
        "reason": "Organizing music is low-effort but gives you a small, satisfying sense of order."
    },
    {
        "name": "Write a pros and cons list about something",
        "description": "Pick any real decision you have coming up and write out the pros and cons.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["journaling", "writing", "planning", "reflection"],
        "tags": ["reflective", "screen_free", "quiet"],
        "reason": "Externalizing a decision frees up the mental RAM you've been using to hold it in your head."
    },
]

_SCREEN_WORK_WORDS = {
    'computer', 'coding', 'code', 'screen', 'design', 'writing', 'office',
    'desk', 'remote', 'laptop', 'developer', 'engineer', 'analyst', 'research',
    'editing', 'student', 'studying', 'homework', 'assignment',
}


def suggest_break_local(date):
    """Rule-based break suggestion using profile + today's tasks + recent task history.
    No API key required."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    today_tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()
    recent_tasks = db.execute(
        "SELECT * FROM tasks WHERE date < ? AND date >= date(?, '-7 days')",
        (date, date)
    ).fetchall()

    hobbies     = (profile['hobbies'] or '').lower()           if profile else ''
    work        = (profile['work_description'] or '').lower()  if profile else ''
    break_style = profile['break_style']                       if profile else 'frequent_short'

    # Detect screen-heavy work from profile
    screen_heavy = any(w in work for w in _SCREEN_WORK_WORDS)

    # Collect task categories from today + recent days for context
    def _cats(tasks):
        return [t['category'].lower() for t in tasks if t['category']]

    today_cats  = _cats(today_tasks)
    recent_cats = _cats(recent_tasks)
    all_cats    = today_cats + recent_cats

    # Dominant category this week (most frequent)
    dominant = max(set(all_cats), key=all_cats.count) if all_cats else None

    # If most tasks are screen/work/study, treat as screen-heavy regardless of profile
    screen_task_words = {'work', 'study', 'school', 'coding', 'homework', 'writing', 'research'}
    if dominant and any(w in dominant for w in screen_task_words):
        screen_heavy = True

    # Fetch names the user has blocked so we can skip them
    blocked_names = {
        row['name'].lower()
        for row in db.execute('SELECT name FROM break_activities WHERE is_blocked = 1').fetchall()
    }

    # Date-based seed so suggestions rotate day to day
    day_seed = int(hashlib.md5(date.encode()).hexdigest(), 16)

    scored = []
    for act in _ACTIVITY_POOL:
        if act['name'].lower() in blocked_names:
            continue
        score = 0.0

        # Hobby keyword match
        for kw in act['hobby_keywords']:
            if kw in hobbies:
                score += 5

        # Boost screen-free activities for screen-heavy workers/days
        if screen_heavy and 'screen_free' in act['tags']:
            score += 3
        # Penalise screen entertainment for screen-heavy days
        if screen_heavy and 'screen' in act['tags'] and 'screen_free' not in act['tags']:
            score -= 3

        # Boost physical/outdoor if today is packed with desk-style tasks
        if screen_heavy and 'physical' in act['tags']:
            score += 2
        if screen_heavy and 'outdoor' in act['tags']:
            score += 1

        scored.append((score, act))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Pick from the top 10 scorers, rotating daily so the same activity
    # doesn't win every day even when it has the highest hobby match.
    top = scored[:10]
    best = top[day_seed % len(top)][1]

    duration = best['short_mins'] if break_style == 'frequent_short' else best['long_mins']

    # Personalise the reason with today's context when possible
    reason = best['reason']
    if dominant and screen_heavy and 'screen_free' in best['tags']:
        reason = f"After a day of {dominant} work, stepping away from your screen will help you recharge. {reason}"
    elif dominant:
        reason = f"With a day focused on {dominant}, {reason[0].lower()}{reason[1:]}"

    return {
        "name": best['name'],
        "description": best['description'],
        "duration_minutes": duration,
        "reason": reason,
    }

_client = None
MODEL_FAST = 'claude-haiku-4-5-20251001'
MODEL_FULL = 'claude-sonnet-4-6'


def _parse_json(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    return json.loads(text.strip())


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not set')
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _format_tasks(tasks):
    if not tasks:
        return 'No tasks scheduled'
    lines = []
    for t in tasks:
        time_str = ''
        if t['start_time']:
            time_str = f" ({t['start_time']}"
            if t['end_time']:
                time_str += f"–{t['end_time']}"
            time_str += ')'
        lines.append(f"- {t['title']}{time_str} [{t['priority']} priority, {t['status']}]")
    return '\n'.join(lines)


def _total_hours(tasks):
    total_min = 0
    for t in tasks:
        if t['start_time'] and t['end_time']:
            sh, sm = map(int, t['start_time'].split(':'))
            eh, em = map(int, t['end_time'].split(':'))
            total_min += (eh * 60 + em) - (sh * 60 + sm)
    return total_min / 60


def analyze_schedule(date):
    """Read today's tasks + profile from DB and ask Claude whether the day is overscheduled
    and whether the user needs a break nudge. Returns a dict with four keys:
    overscheduled (bool), overscheduled_message (str|None),
    needs_break (bool), break_message (str|None)."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()

    total_hours = _total_hours(tasks)

    if profile:
        profile_ctx = (
            f"Name: {profile['name']}\n"
            f"Work: {profile['work_description'] or 'not specified'}\n"
            f"Max daily hours: {profile['max_daily_hours']}\n"
            f"Stress sensitivity: {profile['stress_sensitivity']}\n"
            f"Break style: {profile['break_style']}\n"
            f"Wake: {profile['wake_time'] or 'not set'}, Sleep: {profile['sleep_time'] or 'not set'}"
        )
    else:
        profile_ctx = 'No profile'

    prompt = f"""You are a mindful scheduling assistant for Calmendar, a personal daily planner.

User profile:
{profile_ctx}

Tasks for {date}:
{_format_tasks(tasks)}
Total scheduled time: {total_hours:.1f} hours

Respond with ONLY a JSON object — no markdown, no explanation:
{{
  "overscheduled": true or false,
  "overscheduled_message": "1-2 sentence specific message about why this day is too full, or null if not overscheduled",
  "needs_break": true or false,
  "break_message": "1-2 sentence warm nudge to take a break if schedule is heavy, or null"
}}

Use the user's stress sensitivity and max_daily_hours to judge overscheduling — don't use a fixed threshold.
High-priority or cognitively heavy tasks should lower the threshold. Be warm and specific, not generic."""

    response = _get_client().messages.create(
        model=MODEL_FAST,
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )

    result = json.loads(response.content[0].text)
    # If the day is overscheduled, a break nudge should always show too
    if result.get('overscheduled') and not result.get('needs_break'):
        result['needs_break'] = True
        if not result.get('break_message'):
            result['break_message'] = "With a day this packed, a short break will help you stay focused and finish strong."
    return result


def suggest_break(date):
    """Read today's tasks + profile from DB and ask Claude for a specific, personalized
    break activity suggestion. Returns a dict with name, description, duration_minutes, reason."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()

    if profile:
        break_style_desc = (
            'frequent short breaks (5–10 min)'
            if profile['break_style'] == 'frequent_short'
            else 'infrequent longer breaks (20–30 min)'
        )
        profile_ctx = (
            f"Hobbies: {profile['hobbies'] or 'not specified'}\n"
            f"Break style preference: {break_style_desc}\n"
            f"Work type: {profile['work_description'] or 'not specified'}"
        )
    else:
        profile_ctx = 'No profile'

    prompt = f"""You are a mindful well-being assistant for Calmendar.

User profile:
{profile_ctx}

Today's schedule:
{_format_tasks(tasks)}

Suggest one specific break activity tailored to this person's hobbies and what they've been doing today.
Respond with ONLY a JSON object — no markdown:
{{
  "name": "short activity name",
  "description": "what to do in 1-2 sentences",
  "duration_minutes": number,
  "reason": "why this fits this person right now, 1 sentence"
}}"""

    response = _get_client().messages.create(
        model=MODEL_FAST,
        max_tokens=250,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return _parse_json(response.content[0].text)


def generate_day_summary(date, completed, pending, mood=None, notes=None):
    """Ask Claude to write a warm, specific end-of-day summary grounded in the user's
    actual tasks and reflection notes."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()

    completed_str = '\n'.join(f'- {t["title"]}' for t in completed) if completed else 'none'
    pending_str = '\n'.join(f'- {t["title"]}' for t in pending) if pending else 'none'

    if profile:
        profile_ctx = (
            f"Name: {profile['name']}\n"
            f"Work: {profile['work_description'] or 'not specified'}\n"
            f"Hobbies: {profile['hobbies'] or 'not specified'}"
        )
    else:
        profile_ctx = 'No profile'

    mood_line = f"\nMood today: {mood}/5" if mood else ''
    notes_line = f"\nUser's reflection notes: {notes}" if notes else ''

    prompt = f"""You are a warm, encouraging daily reflection assistant for Calmendar.

User profile:
{profile_ctx}

Date: {date}
Completed tasks:
{completed_str}

Still pending:
{pending_str}{mood_line}{notes_line}

Write a brief, genuine end-of-day summary in 2-3 sentences. Acknowledge specific accomplishments,
address pending work gently and positively, and close with an encouraging thought tailored to this person.
Avoid generic phrases like "great job" — be specific and human."""

    response = _get_client().messages.create(
        model=MODEL_FULL,
        max_tokens=200,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response.content[0].text.strip()

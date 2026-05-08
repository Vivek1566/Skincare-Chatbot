"""
chatbot_nlp.py -- Enhanced Conversational Skincare Chatbot
Improved with natural language processing, better response generation,
and comprehensive skincare knowledge base.
"""

import re
import random

# --- Enhanced Condition Knowledge Base ---
CONDITION_ADVICE = {
    'acne': {
        'cause': 'Acne occurs when hair follicles become clogged with dead skin cells and sebum. Bacteria called P. acnes multiplies, causing inflammation and breakouts. Hormones, genetics, and environmental factors all play a role.',
        'routine': '1. Cleanse twice daily with a salicylic acid wash (2%)\n2. Apply a targeted treatment with benzoyl peroxide or adapalene in the evening\n3. Use a lightweight, non-comedogenic moisturizer\n4. Apply SPF 30+ daily\n5. Exfoliate 2-3 times weekly',
        'ingredients': ['Salicylic Acid (BHA)', 'Benzoyl Peroxide', 'Adapalene (Retinoid)', 'Niacinamide', 'Azelaic Acid'],
        'solutions': 'Keep skin clean but avoid over-washing. Use non-comedogenic products. Avoid picking at pimples. Change pillowcases every 2-3 days.',
        'avoid': 'Thick oils, heavy makeup, fragrance, and picking at the skin',
        'timeline': 'Most treatments take 4-6 weeks to show visible results.'
    },
    'bags': {
        'cause': 'Under-eye bags result from fluid accumulation, lack of sleep, allergies, high salt intake, or aging. Genetics also plays a significant role.',
        'routine': '1. Apply a caffeine-infused eye cream (morning)\n2. Use cold tea bags or jade rollers for 5-10 minutes in the morning\n3. Sleep with head elevated on an extra pillow\n4. Reduce sodium intake\n5. Stay hydrated (drink 8+ glasses of water daily)',
        'ingredients': ['Caffeine', 'Peptides', 'Vitamin K', 'Hyaluronic Acid', 'Retinol (low strength)'],
        'solutions': 'Get 7-9 hours of quality sleep. Use cold compresses immediately upon waking. Consider professional treatments like fillers.',
        'avoid': 'High salt diet, rubbing eyes, and excessive sun exposure',
        'timeline': 'Caffeine products work quickly. Structural changes take weeks of consistent use.'
    },
    'redness': {
        'cause': 'Skin redness comes from rosacea, contact dermatitis, sun damage, irritation, or broken capillaries. Inflammation dilates blood vessels, causing visible redness.',
        'routine': '1. Use a fragrance-free, pH-balanced cleanser\n2. Apply a soothing serum with Centella or Azelaic Acid\n3. Use a barrier-repair moisturizer with ceramides\n4. Apply SPF 50+ daily\n5. Avoid triggers (spicy foods, hot water)',
        'ingredients': ['Azelaic Acid', 'Centella Asiatica (Cica)', 'Niacinamide', 'Panthenol', 'Aloe Vera'],
        'solutions': 'Identify triggers. Avoid physical exfoliation. Use mineral sunscreen. Consider laser or IPL therapy.',
        'avoid': 'Harsh scrubs, fragrance, alcohol-based toners, hot water, and spicy foods',
        'timeline': 'Rosacea management is long-term. Azelaic acid shows results in 2-3 months.'
    },
    'dryness': {
        'cause': 'Dry skin lacks natural lipids and cannot retain moisture. This results from genetics, aging, harsh cleansers, low humidity, or dehydration.',
        'routine': '1. Use a creamy or oil cleanser\n2. Apply hyaluronic acid on damp skin\n3. Seal with a rich night cream with ceramides\n4. Use a facial oil as final step\n5. Use a humidifier, especially at night',
        'ingredients': ['Hyaluronic Acid', 'Ceramides', 'Glycerin', 'Squalane', 'Shea Butter'],
        'solutions': 'Apply moisturizer to damp skin within 3 minutes of cleansing. Use a humidifier. Avoid long hot showers.',
        'avoid': 'Foaming cleansers, alcohol-based products, frequent hot showers, and harsh exfoliation',
        'timeline': 'Noticeable improvement in 3-5 days. Deep hydration takes 2-3 weeks.'
    },
    'aging': {
        'cause': 'Aging accelerates from UV exposure (photoaging), pollution, free radicals, collagen breakdown, and loss of elastin.',
        'routine': '1. Morning: Vitamin C serum + SPF 50+\n2. Night: Retinoid (retinol or tretinoin)\n3. Use peptides to support collagen\n4. Apply rich hydration layers\n5. Use eye cream for delicate area',
        'ingredients': ['Retinol', 'Vitamin C', 'Peptides', 'AHAs', 'Hyaluronic Acid'],
        'solutions': 'Sunscreen is the #1 anti-aging product. Incorporate antioxidants. Get adequate sleep. Exercise regularly.',
        'avoid': 'Unprotected sun exposure, tanning beds, smoking, and poor sleep',
        'timeline': 'Fine line improvement: 4-8 weeks. Significant results: 3-6 months.'
    },
    'oily': {
        'cause': 'Oily skin results from overactive sebaceous glands producing excess sebum. This can be hereditary, hormonal, or worsened by heat and humidity.',
        'routine': '1. Use a lightweight gel or foam cleanser\n2. Apply a mattifying toner\n3. Use lightweight, oil-free moisturizer\n4. Apply niacinamide serum\n5. Use a clay mask 1-2x weekly',
        'ingredients': ['Niacinamide', 'Salicylic Acid', 'Zinc PCA', 'Witch Hazel', 'Tea Tree Oil'],
        'solutions': 'Use blotting papers. Avoid heavy makeup. Use non-comedogenic products. Don\'t over-strip skin.',
        'avoid': 'Heavy oils, thick creams, and heavy makeup',
        'timeline': 'Mattifying effects appear within days. Oil regulation takes 2-3 weeks.'
    },
    'pigmentation': {
        'cause': 'Hyperpigmentation comes from overproduction of melanin, triggered by UV exposure, hormones (melasma), or post-inflammatory responses from acne scars.',
        'routine': '1. Vitamin C serum every morning\n2. Brightening serums with kojic acid or alpha arbutin\n3. Chemical exfoliation with AHAs 3-4x weekly\n4. SPF 50+ daily (non-negotiable)\n5. Weekly targeted mask',
        'ingredients': ['Vitamin C', 'Alpha Arbutin', 'Tranexamic Acid', 'Kojic Acid', 'Glycolic Acid'],
        'solutions': 'Consistent use of brighteners (3-4 months minimum). Never skip SPF. Consider professional treatments like laser.',
        'avoid': 'Tanning beds and unprotected sun exposure',
        'timeline': 'Slow improvement; dark spots take 2-3 months to fade with consistency.'
    },
    'eczema': {
        'cause': 'Eczema (Atopic Dermatitis) is a condition where the skin barrier is weak, allowing moisture to escape and irritants to enter, leading to inflammation and severe itchiness.',
        'routine': '1. Wash with lukewarm water and a soap-free, gentle cleanser\n2. Apply a thick ointment or ceramide cream within 3 minutes of bathing\n3. Use colloidal oatmeal to soothe flare-ups',
        'ingredients': ['Ceramides', 'Colloidal Oatmeal', 'Glycerin', 'Shea Butter', 'Panthenol'],
        'solutions': 'Use a humidifier. Wear 100% cotton clothing. Avoid fragranced detergents and skincare. Seek a dermatologist for prescription steroids if needed.',
        'avoid': 'Fragrance, essential oils, hot water, harsh soaps, scratching, and wool clothing',
        'timeline': 'Flare-ups can subside in 1-3 weeks with proper barrier repair and trigger avoidance.'
    },
    'fungal acne': {
        'cause': 'Fungal acne (Malassezia folliculitis) is not true acne. It is caused by an overgrowth of yeast in the hair follicles, often triggered by heat, humidity, and sweating.',
        'routine': '1. Cleanse with an antifungal shampoo (e.g., ketoconazole) left on for 5 mins as a mask\n2. Use a fungal-acne safe, lightweight moisturizer\n3. Shower immediately after sweating',
        'ingredients': ['Ketoconazole', 'Zinc Pyrithione', 'Sulfur', 'Squalane', 'Salicylic Acid'],
        'solutions': 'Switch to a 100% fungal-acne safe routine. Avoid oils with fatty acids and esters.',
        'avoid': 'Most plant oils, polysorbates, esters (ingredients ending in -ate), and fermented skincare',
        'timeline': 'Improvement is often seen rapidly (within 1-2 weeks) when using targeted antifungals.'
    },
    'melasma': {
        'cause': 'Melasma causes brown or gray-brown patches on the face. It is primarily triggered by hormonal changes (like pregnancy or birth control) and UV exposure from the sun.',
        'routine': '1. Apply a high-protection mineral SPF daily\n2. Use Tyrosinase inhibitors like Tranexamic Acid or Alpha Arbutin\n3. Incorporate gentle AHAs for cell turnover',
        'ingredients': ['Tranexamic Acid', 'Alpha Arbutin', 'Vitamin C', 'Kojic Acid', 'Zinc Oxide (Mineral SPF)'],
        'solutions': 'Sun protection is non-negotiable. Wear wide-brimmed hats. Visible light (including from screens) can also worsen it, so iron oxides in tinted SPF are helpful.',
        'avoid': 'Unprotected sun exposure, excessive heat (like saunas), and harsh irritating products',
        'timeline': 'Melasma is notoriously stubborn; significant fading takes 3-6 months of strict consistency.'
    },
    'sunburn': {
        'cause': 'Sunburn is acute skin damage from overexposure to ultraviolet (UV) radiation, leading to inflammation, redness, pain, and potentially peeling.',
        'routine': '1. Take cool baths or showers\n2. Apply pure aloe vera gel or soothing moisturizers\n3. Drink extra water to prevent dehydration\n4. Avoid sun exposure until fully healed',
        'ingredients': ['Aloe Vera', 'Centella Asiatica', 'Panthenol', 'Ceramides'],
        'solutions': 'Take a cool shower immediately. Do not pop any blisters. Apply a cool compress.',
        'avoid': 'Further sun exposure, hot water, harsh scrubs, active acids (AHAs/BHAs), and retinoids',
        'timeline': 'Redness peaks in 12-24 hours and subsides over 3-5 days. Peeling may occur for up to a week.'
    },
    'blackheads': {
        'cause': 'Blackheads are open comedones where a pore becomes clogged with sebum and dead skin cells. The dark color is from the oxidation of the melanin in the debris when exposed to air.',
        'routine': '1. Double cleanse daily\n2. Exfoliate with 2% Salicylic Acid (BHA)\n3. Use a clay mask once a week\n4. Use non-comedogenic moisturizers',
        'ingredients': ['Salicylic Acid', 'Clay (Kaolin/Bentonite)', 'Niacinamide', 'Retinoids'],
        'solutions': 'Consistency with BHA is key. Avoid pore strips as they can stretch pores and cause micro-tears.',
        'avoid': 'Pore strips, squeezing them out, thick occlusive oils',
        'timeline': 'Takes 2-4 weeks of consistent BHA use to see clear improvement.'
    }
}

# --- Expanded Ingredient Knowledge Base ---
INGREDIENT_INFO = {
    'salicylic acid': 'A BHA (Beta Hydroxy Acid) that dissolves oil and unclogs pores. Perfect for acne and oily skin. Use 0.5-2% concentration.',
    'hyaluronic acid': 'A humectant that holds moisture in skin. Can hold 1000x its weight in water! Best applied to damp skin.',
    'retinol': 'A Vitamin A derivative that boosts collagen and cell turnover. Reduces wrinkles and acne. Requires gradual introduction.',
    'vitamin c': 'A powerful antioxidant that brightens skin and protects against pollution. Use 10-20% for visible results.',
    'ceramides': 'Essential lipids (50% of skin barrier) that repair and strengthen barrier. Prevents water loss.',
    'niacinamide': 'Vitamin B3 that regulates oil, minimizes pores, calms redness. Works with almost all ingredients.',
    'azelaic acid': 'A multi-tasking acid for acne, redness, and pigmentation. Great for rosacea. Use 10-20%.',
    'alpha arbutin': 'A safe skin brightener that targets melanin production. Results visible in 2-3 months.',
    'caffeine': 'Reduces puffiness and under-eye bags by improving circulation. Works best in eye creams.',
    'peptides': 'Protein building blocks that signal collagen and elastin production. Supports skin firmness.',
    'panthenol': 'Pro-vitamin B5 that soothes and repairs. Safe for sensitive skin and all types.',
    'cica': 'Centella Asiatica - extremely soothing for inflamed skin. Nature\'s first aid kit for sensitivity.',
    'glycerin': 'A humectant that draws moisture. Non-irritating and works for all skin types.',
    'squalane': 'Lightweight, non-comedogenic oil similar to skin sebum. Won\'t clog pores.',
    'glycolic acid': 'An AHA (Alpha Hydroxy Acid) that exfoliates the surface layer of skin. Great for anti-aging and hyperpigmentation. Increases sun sensitivity.',
    'lactic acid': 'A gentler AHA than glycolic acid, it exfoliates while also providing hydration. Perfect for dry or sensitive skin.',
    'zinc oxide': 'A physical sunscreen filter that sits on top of the skin to block UV rays. Also highly soothing and anti-inflammatory.',
    'snail mucin': 'A powerhouse ingredient for hydration, barrier repair, and soothing irritation. Gives a famous "glass skin" glow.',
    'green tea': 'Rich in antioxidants, specifically EGCG. It reduces inflammation, controls oil production, and protects against free radicals.',
    'benzoyl peroxide': 'A powerful antibacterial treatment that kills acne-causing bacteria. Can be drying, so start with 2.5% or 5% strengths.',
    'urea': 'At lower concentrations (under 10%), it acts as a superior humectant. At higher concentrations, it acts as a gentle exfoliant.'
}

# --- Chat Replies ---
GREETING_REPLIES = [
    "Hello! I'm your AI Skincare Expert. How can I help you achieve glowing skin today?",
    "Hi there! I'm Glow.AI. Ask me about your skin analysis, specific ingredients, or routines!",
    "Greetings! Ready to solve your skincare concerns. What would you like to know?",
    "Hey! I'm here to help you build the perfect routine. What's on your mind?",
    "Welcome! I'm your dedicated skincare assistant. What can I help with?",
]

FALLBACK_REPLIES = [
    "That's interesting! Try asking about specific skin conditions, ingredients, or routines for detailed advice.",
    "I'm specialized in skincare. Try 'What causes acne?' or 'How does retinol work?' for detailed answers.",
    "I might need more details. Are you asking about a condition, ingredient, or skincare routine?",
    "I'm here to help with skincare topics! Ask me about conditions or ingredients like niacinamide.",
    "Not sure about that, but I'd love to help with skincare! What's your skincare concern?",
]

# --- Helper Patterns for Efficiency ---
PATTERN_MAP = {
    'cause': re.compile(r'\b(cause|why|reason|how come|trigger|what causes)\b', re.I),
    'routine': re.compile(r'\b(routine|step|how to|treat|fix|help|manage|care|regimen)\b', re.I),
    'ingredient': re.compile(r'\b(ingredient|product|use|apply|contain|active|what is|tell me)\b', re.I),
    'solution': re.compile(r'\b(solution|solve|fix|remedy|tip|advice|help|recommend)\b', re.I),
    'avoid': re.compile(r'\b(avoid|bad|stop|not use|worse|danger)\b', re.I),
    'timeline': re.compile(r'\b(how long|timeline|when|results|weeks|months)\b', re.I),
}

def _normalise(text: str) -> str:
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower()).strip()

def handle_chat(message: str, context: dict = None) -> str:
    """
    Highly efficient chat handler with expanded knowledge and solutions.
    """
    if context is None:
        context = {}
    
    msg = _normalise(message)
    
    # 1. Quick Greetings Check
    greet_words = {'hello', 'hi', 'hey', 'greetings', 'morning', 'evening', 'yo'}
    msg_words = set(msg.split())
    if msg_words.intersection(greet_words) and len(msg_words) <= 3:
        return random.choice(GREETING_REPLIES)

    # 1.5 Appreciation and Small Talk
    appreciation_words = {'thanks', 'thank', 'appreciate', 'great', 'awesome', 'amazing', 'perfect', 'good'}
    if msg_words.intersection(appreciation_words) and len(msg_words) <= 5:
        return "You're very welcome! I'm glad I could help. Let me know if you have any other questions about skincare."
        
    if 'how are you' in msg or 'how are u' in msg or 'how do you do' in msg:
        return "I'm doing great, thank you for asking! I'm your Glow.AI skincare assistant, fully powered up and ready to help you achieve your skincare goals. What's on your mind today?"


    # 2. Skin Type Check
    if any(w in msg for w in ['oily', 'combination', 'greasy']):
        return "For **oily skin**, focus on BHA (Salicylic Acid) to control sebum and lightweight gel moisturisers. Avoid heavy creams!"
    
    if any(w in msg for w in ['dry', 'flaky', 'tight']):
        return "For **dry skin**, use cream cleansers and rich moisturisers with Ceramides. Apply products on damp skin to lock in moisture."

    # 3. Ingredient Lookup (Priority)
    for ing, info in INGREDIENT_INFO.items():
        if ing in msg:
            return f"**{ing.title()}**: {info}"

    # 4. Condition Lookup
    condition_matched = None
    for cond in CONDITION_ADVICE:
        if cond in msg:
            condition_matched = cond
            break
    
    # Fallback to context
    if not condition_matched and 'last_condition' in context:
        lc = str(context['last_condition']).lower()
        if lc in CONDITION_ADVICE:
            condition_matched = lc

    if condition_matched:
        info = CONDITION_ADVICE[condition_matched]
        cond_name = condition_matched.title()
        
        # Determine specific intent
        if PATTERN_MAP['cause'].search(msg):
            return f"**What causes {cond_name}?**\n{info['cause']}"
        
        if PATTERN_MAP['solution'].search(msg) or PATTERN_MAP['routine'].search(msg):
            return (f"**Solutions for {cond_name}:**\n{info['solutions']}\n\n"
                    f"**Recommended Routine:**\n{info['routine']}\n\n"
                    f"**Best Ingredients:** {', '.join(info['ingredients'])}")
        
        if PATTERN_MAP['avoid'].search(msg):
            return f"**What to avoid with {cond_name}:**\n{info['avoid']}"
        
        # Default Overview
        return (f"**{cond_name} Analysis & Advice**\n\n"
                f"**Cause:** {info['cause']}\n\n"
                f"**Routine:** {info['routine']}\n\n"
                f"**Ingredients:** {', '.join(info['ingredients'])}\n\n"
                f"**Pro Tip:** {info['solutions']}")

    # 5. General Routine/SPF Logic
    if any(w in msg for w in ['routine', 'morning', 'night', 'steps']):
        return ("**The Gold Standard Routine:**\n\n"
                "**AM (Protect)**: Gentle Cleanser -> Vitamin C -> Moisturiser -> SPF 50\n"
                "**PM (Treat)**: Double Cleanse -> Targeted Active (Retinol/Acid) -> Barrier Cream\n\n"
                "Upload your photo for a scan-based routine tailored to you!")

    if any(w in msg for w in ['spf', 'sunscreen', 'sun', 'uv']):
        return ("**SPF is your #1 Defense!**\n\n"
                "Sun damage causes 80% of visible aging and hyperpigmentation. Use a broad-spectrum SPF 30+ daily, even if it's cloudy or you're indoors.")

    # 6. Fallback
    return random.choice(FALLBACK_REPLIES)

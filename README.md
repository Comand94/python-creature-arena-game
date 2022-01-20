# python-creature-arena-game
A strategic game against AI where you command your creatures in Pokemon-style battles.

BELOW ARE MOST FEATURES AS OF 20.01.2022

Game window features:
* Resizable window which keeps 16:9 ratio
   (all art and fonts are scaled and their positions are scaled to match new window size)

Menu features:
* Main menu
* Match settings menu
* Active semi-transparent pause menu with instant settings (ESC button)
    it allows returning to main menu, speeding up in-game delays and animations and skipping animations all-together

Game modes:
* Creature Index for browsing available creatures (no end, this is a peaceful mode)
* Standard mode with following options: 
*   Player vs Player, AI vs Player, Player vs AI
*   AI level between 0 and 10 (changes behaviour and creature bonuses)
*   Up to 3 creatures per player total, a new creature comes on when previous is defeated

Creatures and abilities:
* 5 unique creatures
* 6 unique abilities per creature
* 1 universal ability (Health Kit)
* 19 unique status effects
* 2 malleable status effects for each possible AI player (what they do depends on AI level)

Art and animations:
* 2 original creatures with aninimated sprites (5 frames per creature)
* 3 WIP creatures with animated sprites (5 frames per creature)
* battle text box with animated sprite (10 frames)
* visualized hit chance and status chance rolling (numbers that change quickly then slower and slower until stop)
* icon art for all abilities and status effects (except rage abilities)
* HUD including info box, type box, creature box and selected ability/status frames
* font (downloaded from https://www.1001freefonts.com/good-times.font)

User interaction during battle pre-turn phase:
* choose abilities discretely via keyboard to allow for fair hot-seat (local) versus
*   all button tooltips are displayed when they are needed
* infobox which describes abilities, their statuses and active effects for both players' creatures, available individually for both players
* typebox which works like the infobox, but describes both players' creature types and allows checking type relationships
* creaturebox which works like infobox, but describes both players' creature rosters in order (name and health)

Creature, move and status mechanics:
* targeting self or enemy with a move
* move speed between 1 (slowest) and 5 (fastest) which decides which moves are made first during a turn
   in case of draw, it's randomized who makes the move first
* type which describes creatures, moves and effects
   depending on type, damage (and status chance) is multiplied and effects of certain type can be removed from target
* health and max health, rage and max rage 
   (rage is increased for taking damage and can be used for special abilities) which describe creatures
* damage (range) or healing (range) which can be applied by various moves
* damage over time (range) or healing over time (range) which can be applied by various effects
* hit chance or miss chance which describe abilities and can be boosted by various effects
   moves that do not hit will either miss entirely or graze (apply some damage/healing, but no status will be applied)
* dodge chance or negative dodge chance which describe creatures and can be boosted by various effects
* hit attempts which describes how many times a move will try to connect
*   this allows triggering more than 1 status effects during a round among other things
* status effect (and status effect chance) which describes what status effect can be triggered by move on targetted enemy
* cooldown which describes how long abilities will be unavailable after use 
   (in case of health kit it's starting cooldown is also it's max cooldown and not 0)
* rage cost which describes rage cost of an ability (used for rage abilities)
* aim and dodge modifiers (negative or positive) which describe effects
* damage modifier (for all types of moves or one specific type) 
    which describes damage bonus or penalty for using attacks while under an effect with this modifier
* status duration which describes effect's duration (0 means current turn only)
* stun duration which describes for how many turns a target will be unable to make moves when this effect is applied to him/her 
   (-1 means no stun, 0 means current turn only)
* thorn damage (range) or leech amount (range) 
   which describes damage taken/health healed for attacking (in case of leech, hitting) an enemy who has an active effect with this stat
   
With these statistics, a lot of different moves and interactions can be created.
Some of the more interesting ones are a self-damaging, self-stunning move RESET VOID for SHIGOWU which removes all effects from the creature and deals huge damage to enemy if it attacks SHIGOWU during this turn and consecutive turn when it's stunned. Another move I really like is BAMAT's DROP OF BLOOD, which deals 1 damage and can't be avoided unless using a very powerful dodging move (SHIGOWU's ESCAPE TO VOID) and applies guarnateed defense debuff alongside with negative thorn damage (leech amount on hit) to enemy. There are no moves that heal the enemy yet, but even that is possible (i.e. heal an enemy, but debuff him)!

Rage adds another layer to strategy, because it adds an extra move to creature's arsenal when situation is dire and a lot of health has been lost. Sometimes rage moves are really powerful, other times they become powerful when combined with other moves (for example, BAMAT's rage move MAGIC BOLTS attacks twice, so it gains double benefit from damage buff that MAGICAL REINFORCEMENT [which is the only 0 cooldown move currently other than rage moves] provides). 

AI Features:
* AI penalties (AI level 0-4)
* AI bonuses (AI level 6-10)
* rate it's available moves vs opponent's
* make mistake in rating (AI level 0-4)
* rate moves which haven't been used a while higher than other moves (this is called novelty bonus)
   max novelty factor is influenced by AI level (smarter AI favor novel moves less, they care about efficiency more)
* choose a random move (AI level 0)
* choose between two best average moves (weighted randomization)
* choose the best counter move to the best opponent average move 
   (if the AI guesses correctly the move opponent will use, it will reinforce this behaviour and do it more often, otherwise it will be doubly less likely to repeat it)
* choose the best counter move to the best opponent counter move to your best counter move 
   (if the AI guesses correctly the move opponent will use, it will reinforce this behaviour and do it more often, otherwise it will be doubly less likely to repeat it)
* a move which is likely to kill has bonus score, a move which is likely to result in suicide has bonus negative score
* long-lasting status effects which might not see their full potential due to the game ending are rated lower
* extinguishing active effects can affect score positively or negatively depending on effect and target
* all move statistics and effect statistics affect the move score
* when stats stack over 100% they begin to be mostly ignored by the scoring algorithm (i.e. hit chance beyond 110 is cut off)
* some moves against some creatures have special score multiplier to take into account other things which scoring algorithm might miss


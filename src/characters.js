import atlasCombatBounds from './atlas-combat-bounds.json';
import aetherCombatBounds from './aether-combat-bounds.json';
import seraphCombatBounds from './seraph-combat-bounds.json';
import roninCombatBounds from './ronin-combat-bounds.json';
import roninMotionBounds from './ronin-motion-bounds.json';
import seraphMotionBounds from './seraph-motion-bounds.json';
import scorpioMotionBounds from './scorpio-motion-bounds.json';

export const characters = {
  'atlas-09': {
    name: 'ATLAS', number: '09', model: `${import.meta.env.BASE_URL}models/atlas-09.glb?v=7`, concept: `${import.meta.env.BASE_URL}concept.png`,
    className: 'VETERAN CLASS / HEAVY MECHA', height: '18.0', condition: 'HEAVILY WORN',
    tagline: ['Seen better days.', 'Still standing.'],
    description: ['Scarred armor. Exposed machinery.', 'A reactor that refuses to go dark.'],
    caption: 'FIELD-WORN / OPERATIONAL', study: '001', conceptTitle: 'Built from a battle scar.',
    conceptAlt: 'Original ATLAS concept with battered olive armor and a cyan chest reactor',
    accent: '#d5f3a5', reactorLightIntensity: 3, motionBounds: atlasCombatBounds,
    motionOrder: ['Sentinel','Walk','Run','PunchCombo','HitChest','HitHead','Knockback','KneelFire','Backflip','Collapse'],
  },
  'aether-02': {
    name: 'AETHER', number: '02', model: `${import.meta.env.BASE_URL}models/aether-02.glb?v=7`, concept: `${import.meta.env.BASE_URL}concept-aether-02.png`,
    className: 'VELOCITY CLASS / ATHLETIC MECHA', height: '14.0', condition: 'WHITE STEEL / OPAQUE GLASS',
    tagline: ['Built for motion.', 'Made of light.'],
    description: ['Sculpted white steel. Smoked glass.', 'Precision in every stride.'],
    caption: 'AGILE FRAME / OPERATIONAL', study: '002', conceptTitle: 'The shape of velocity.',
    conceptAlt: 'Original athletic AETHER concept with streamlined white steel and opaque smoky glass panels',
    accent: '#bde9f6', reactorLightIntensity: 0, motionBounds: aetherCombatBounds,
    motionOrder: ['Sentinel','Walk','Run','PunchCombo','DodgeRoll','HitChest','HitHead','Knockback','KneelFire','Backflip','Collapse'],
  },
  'seraph-03': {
    name: 'SERAPH', number: '03', model: `${import.meta.env.BASE_URL}models/seraph-03.glb?v=2`, concept: `${import.meta.env.BASE_URL}concept-seraph-03.png`,
    className: 'AERIAL CLASS / WINGED MECHA', height: '20.0', condition: 'TITANIUM / SILVER WINGS',
    tagline: ['Steel in the sky.', 'Thunder in its arm.'],
    description: ['Articulated metal wings.', 'An integrated heavy cannon.'],
    caption: 'AERIAL FRAME / CANNON ARM', study: '003', conceptTitle: 'Forged for the sky.',
    conceptAlt: 'Original winged SERAPH mecha with silver metal wings, dark titanium armor, amber lighting and a huge cannon replacing its right arm',
    accent: '#ffd09a', reactorLightIntensity: 0, displayReferenceHeight: 15.5, fogDensity:.014, inspectionFill:1.2,
    motionOrder: ['Sentinel','Run','KneelFire','Backflip','WingDeploy','Flight','HitChest','HitHead','Knockback'],
    motionBounds: {...seraphMotionBounds,...seraphCombatBounds},
    effects: {color:'#ffc171',flashColor:'#ffe5b0',radius:.075,length:1.8,flashRadius:.3,interval:.64,useMuzzleDirection:true,muzzleAxis:[0,-1,0]},
  },
  'ronin-04': {
    name:'RONIN', number:'04', model:`${import.meta.env.BASE_URL}models/ronin-04.glb?v=13`, concept:`${import.meta.env.BASE_URL}concept-ronin-04.png`,
    className:'SAMURAI CLASS / BLADE MECHA', height:'16.0', condition:'CRIMSON LACQUER / AGED GOLD',
    tagline:['A quiet resolve.','An unbroken blade.'], description:['Layered steel. A crescent of gold.','Precision at the edge of battle.'],
    caption:'SAMURAI FRAME / KATANA', study:'004', conceptTitle:'Discipline, cast in steel.',
    conceptAlt:'Original RONIN samurai mecha with crimson armor, a gold crescent helmet and a long katana',
    accent:'#f3b39b', reactorLightIntensity:0, fogDensity:.014, inspectionFill:1.2,
    motionOrder:['Sentinel','BladeSalute','SwordSlash','SwordCombo','SwordBlock','PunchCombo','Run','HitChest','HitHead','Knockback','KneelFire','Backflip'], motionBounds:{...roninMotionBounds,...roninCombatBounds},
    effects:{muzzleName:'Muzzle_L',forearmName:'forearmL',handName:'handL',color:'#ffcc83',flashColor:'#ffe8b8',interval:.48,useMuzzleDirection:true,muzzleAxis:[0,-1,0]},
  },
  'scorpio-05': {
    name: 'SCORPIO', number: '05', model: `${import.meta.env.BASE_URL}models/scorpio-05.glb?v=3`, concept: `${import.meta.env.BASE_URL}concept-scorpio-05.png`,
    className: 'PREDATOR CLASS / SCORPION MECHA', height: '17.0', condition: 'BLACKENED CHITIN / VENOM EMISSION',
    tagline: ['Predator of the dunes.', 'Silent sting.'],
    description: ['Hydraulic pincer claws. Segmented plasma tail.', 'Built for ambush and lethal precision.'],
    caption: 'PREDATOR FRAME / STINGER', study: '005', conceptTitle: 'Nature’s lethality, mechanized.',
    conceptAlt: 'Original SCORPIO predator mecha with blackened chitin armor, hydraulic pincer claws, and an arched stinger tail',
    accent: '#52ff83', reactorLightIntensity: 0, displayReferenceHeight: 16.0, fogDensity: .014, inspectionFill: 1.2,
    motionOrder: ['Sentinel', 'StingerStrike', 'ClawSlash', 'Run', 'KneelFire', 'Backflip'],
    motionBounds: scorpioMotionBounds,
    effects: {
      muzzleName: 'Muzzle_Stinger',
      color: '#52ff83',
      flashColor: '#d6ffd6',
      radius: .075,
      length: 1.8,
      flashRadius: .32,
      interval: .48,
      useMuzzleDirection: true,
      muzzleAxis: [0, -1, 0]
    },
  },
};

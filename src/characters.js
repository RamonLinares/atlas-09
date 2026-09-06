import roninMotionBounds from './ronin-motion-bounds.json';
import seraphMotionBounds from './seraph-motion-bounds.json';

export const characters = {
  'atlas-09': {
    name: 'ATLAS', number: '09', model: `${import.meta.env.BASE_URL}models/atlas-09.glb?v=6`, concept: `${import.meta.env.BASE_URL}concept.png`,
    className: 'VETERAN CLASS / HEAVY MECHA', height: '18.0', condition: 'HEAVILY WORN',
    tagline: ['Seen better days.', 'Still standing.'],
    description: ['Scarred armor. Exposed machinery.', 'A reactor that refuses to go dark.'],
    caption: 'FIELD-WORN / OPERATIONAL', study: '001', conceptTitle: 'Built from a battle scar.',
    conceptAlt: 'Original ATLAS concept with battered olive armor and a cyan chest reactor',
    accent: '#d5f3a5', reactorLightIntensity: 3,
  },
  'aether-02': {
    name: 'AETHER', number: '02', model: `${import.meta.env.BASE_URL}models/aether-02.glb?v=6`, concept: `${import.meta.env.BASE_URL}concept-aether-02.png`,
    className: 'VELOCITY CLASS / ATHLETIC MECHA', height: '14.0', condition: 'WHITE STEEL / OPAQUE GLASS',
    tagline: ['Built for motion.', 'Made of light.'],
    description: ['Sculpted white steel. Smoked glass.', 'Precision in every stride.'],
    caption: 'AGILE FRAME / OPERATIONAL', study: '002', conceptTitle: 'The shape of velocity.',
    conceptAlt: 'Original athletic AETHER concept with streamlined white steel and opaque smoky glass panels',
    accent: '#bde9f6', reactorLightIntensity: 0,
  },
  'seraph-03': {
    name: 'SERAPH', number: '03', model: `${import.meta.env.BASE_URL}models/seraph-03.glb?v=1`, concept: `${import.meta.env.BASE_URL}concept-seraph-03.png`,
    className: 'AERIAL CLASS / WINGED MECHA', height: '20.0', condition: 'TITANIUM / SILVER WINGS',
    tagline: ['Steel in the sky.', 'Thunder in its arm.'],
    description: ['Articulated metal wings.', 'An integrated heavy cannon.'],
    caption: 'AERIAL FRAME / CANNON ARM', study: '003', conceptTitle: 'Forged for the sky.',
    conceptAlt: 'Original winged SERAPH mecha with silver metal wings, dark titanium armor, amber lighting and a huge cannon replacing its right arm',
    accent: '#ffd09a', reactorLightIntensity: 0, displayReferenceHeight: 15.5, fogDensity:.014, inspectionFill:1.2,
    motionOrder: ['Sentinel','Run','KneelFire','Backflip','WingDeploy','Flight'],
    motionBounds: seraphMotionBounds,
    effects: {color:'#ffc171',flashColor:'#ffe5b0',radius:.075,length:1.8,flashRadius:.3,interval:.64,useMuzzleDirection:true,muzzleAxis:[0,-1,0]},
  },
  'ronin-04': {
    name:'RONIN', number:'04', model:`${import.meta.env.BASE_URL}models/ronin-04.glb?v=2`, concept:`${import.meta.env.BASE_URL}concept-ronin-04.png`,
    className:'SAMURAI CLASS / BLADE MECHA', height:'16.0', condition:'CRIMSON LACQUER / AGED GOLD',
    tagline:['A quiet resolve.','An unbroken blade.'], description:['Layered steel. A crescent of gold.','Precision at the edge of battle.'],
    caption:'SAMURAI FRAME / KATANA', study:'004', conceptTitle:'Discipline, cast in steel.',
    conceptAlt:'Original RONIN samurai mecha with crimson armor, a gold crescent helmet and a long katana',
    accent:'#f3b39b', reactorLightIntensity:0, fogDensity:.014, inspectionFill:1.2,
    motionOrder:['Sentinel','BladeSalute','SwordSlash','Run','KneelFire','Backflip'], motionBounds:roninMotionBounds,
    effects:{muzzleName:'Muzzle_L',forearmName:'forearmL',handName:'handL',color:'#ffcc83',flashColor:'#ffe8b8',interval:.48,useMuzzleDirection:true,muzzleAxis:[0,-1,0]},
  },
};

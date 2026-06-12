// FlowIQ Neural Premium Theme — backgrounds 4K por categoria de jogo
// Coloque os .jpg em assets/backgrounds/. RN escolhe @2x/@3x automaticamente.
import { ImageSourcePropType } from 'react-native';

export const Backgrounds: Record<string, ImageSourcePropType> = {
  paywall:    require('../assets/backgrounds/paywall_hero.jpg'),
  onboarding: require('../assets/backgrounds/onboarding_hero.jpg'),
  memory:     require('../assets/backgrounds/bg_memory.jpg'),
  focus:      require('../assets/backgrounds/bg_focus.jpg'),
  logic:      require('../assets/backgrounds/bg_logic.jpg'),
  math:       require('../assets/backgrounds/bg_math.jpg'),
  speed:      require('../assets/backgrounds/bg_speed.jpg'),
  iq:         require('../assets/backgrounds/bg_iq.jpg'),
};

export const Palette = {
  navy:   '#0A0E27',
  violet: '#7C3AED',
  cyan:   '#22D3EE',
  gold:   '#F59E0B',
  glass:  'rgba(255,255,255,0.08)',
  glassBorder: 'rgba(255,255,255,0.16)',
};

// Wrapper sugerido por tela de jogo:
// <ImageBackground source={Backgrounds[gameCategory]} style={{flex:1}}>
//   <View style={{flex:1, backgroundColor:'rgba(10,14,39,0.35)'}}>{children}</View>
// </ImageBackground>

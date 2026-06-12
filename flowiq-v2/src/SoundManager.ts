// FlowIQ Premium Sound System — drop-in module
// deps: expo-av (já no projeto Expo). Coloque os .m4a em assets/audio/
import { Audio } from 'expo-av';

const FILES = {
  tap:      require('../assets/audio/sfx_tap.m4a'),
  correct:  require('../assets/audio/sfx_correct.m4a'),
  wrong:    require('../assets/audio/sfx_wrong.m4a'),
  combo:    require('../assets/audio/sfx_combo.m4a'),
  levelup:  require('../assets/audio/sfx_levelup.m4a'),
  victory:  require('../assets/audio/sfx_victory.m4a'),
  menu:     require('../assets/audio/music_menu_loop.m4a'),
};

class SoundManager {
  private pool: Record<string, Audio.Sound[]> = {};
  private music: Audio.Sound | null = null;
  private enabled = true;

  async init() {
    await Audio.setAudioModeAsync({ playsInSilentModeIOS: true, staysActiveInBackground: false });
    // Pré-carrega SFX (pool de 2 instâncias p/ rapid-fire sem cortar)
    for (const k of ['tap','correct','wrong','combo','levelup','victory'] as const) {
      this.pool[k] = await Promise.all([0,1].map(async () => {
        const { sound } = await Audio.Sound.createAsync(FILES[k], { volume: 0.9 });
        return sound;
      }));
    }
  }

  play(name: keyof typeof FILES) {
    if (!this.enabled || !this.pool[name]) return;
    const s = this.pool[name].shift()!;
    this.pool[name].push(s);
    s.replayAsync().catch(() => {});
  }

  async startMenuMusic(volume = 0.35) {
    if (this.music) return;
    const { sound } = await Audio.Sound.createAsync(FILES.menu, { isLooping: true, volume });
    this.music = sound;
    await sound.playAsync();
  }
  async stopMenuMusic() { await this.music?.stopAsync(); await this.music?.unloadAsync(); this.music = null; }
  setEnabled(v: boolean) { this.enabled = v; if (!v) this.stopMenuMusic(); }
}

export const Sounds = new SoundManager();
// Uso: await Sounds.init() no App mount; Sounds.play('correct'); Sounds.startMenuMusic();

<template>
  <div class="avatar-wrap">
    <canvas ref="canvasRef" class="avatar-canvas"></canvas>
    <div class="emotion-tag">emotion: {{ emotion }}</div>
    <div v-if="loadError" class="emotion-tag" style="bottom: 42px; color: #b42318">{{ loadError }}</div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as PIXI from 'pixi.js'
import { Live2DModel } from 'pixi-live2d-display/cubism4'

const props = defineProps({
  emotion: { type: String, default: 'neutral' }
})

const canvasRef = ref(null)
const loadError = ref('')
let app
let model

const expressionMap = {
  neutral: 'exp_01',
  happy: 'exp_02',
  sad: 'exp_03',
  angry: 'exp_04',
  shy: 'exp_05',
  surprised: 'exp_06'
}

async function setExpression(emotion) {
  if (!model) return
  const exp = expressionMap[emotion] || expressionMap.neutral
  const manager = model.internalModel?.motionManager?.expressionManager
  if (manager && manager.definitions) {
    const hit = manager.definitions.find((d) => d.Name === exp)
    if (hit) manager.setExpression(exp)
  }
}

function fitModelToCanvas() {
  if (!app || !model) return
  const rw = app.renderer.width
  const rh = app.renderer.height
  if (!model.width || !model.height) return

  const targetWidth = rw * 0.78
  const targetHeight = rh * 0.92
  const scale = Math.min(targetWidth / model.width, targetHeight / model.height)
  model.scale.set(scale)
  model.x = rw * 0.5
  model.y = rh * 0.56
}

onMounted(async () => {
  try {
    if (!window.Live2DCubismCore) {
      throw new Error('未加载 live2dcubismcore.min.js')
    }

    Live2DModel.registerTicker(PIXI.Ticker)

    app = new PIXI.Application({
      view: canvasRef.value,
      width: canvasRef.value.clientWidth || 520,
      height: canvasRef.value.clientHeight || 620,
      backgroundAlpha: 0,
      antialias: true,
      resizeTo: canvasRef.value.parentElement
    })

    model = await Live2DModel.from('/models/mao_pro_en/runtime/mao_pro.model3.json', {
      autoUpdate: true,
      autoInteract: false
    })
    model.anchor.set(0.5, 0.5)
    app.stage.addChild(model)
    fitModelToCanvas()
    app.renderer.on('resize', fitModelToCanvas)
    setExpression(props.emotion)
  } catch (err) {
    loadError.value = `Live2D加载失败: ${err?.message || err}`
    console.error(err)
  }
})

onUnmounted(() => {
  if (app?.renderer) {
    app.renderer.off('resize', fitModelToCanvas)
  }
  if (app) {
    app.destroy(true, { children: true, texture: false, baseTexture: false })
  }
})

watch(
  () => props.emotion,
  (v) => setExpression(v)
)
</script>

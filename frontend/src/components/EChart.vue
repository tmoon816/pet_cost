<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
})

const containerRef = ref(null)
let chart = null
let resizeObserver = null

function handleWindowResize() {
  if (chart) chart.resize()
}

onMounted(() => {
  if (!containerRef.value) return
  chart = echarts.init(containerRef.value)
  chart.setOption(props.option)

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => chart && chart.resize())
    resizeObserver.observe(containerRef.value)
  } else {
    window.addEventListener('resize', handleWindowResize)
  }
})

watch(
  () => props.option,
  (val) => {
    if (chart && val) chart.setOption(val, true)
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  window.removeEventListener('resize', handleWindowResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div ref="containerRef" class="echart-container" />
</template>

<style scoped>
.echart-container {
  width: 100%;
  height: 100%;
}
</style>

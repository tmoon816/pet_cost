<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCostStore } from '@/stores/costStore'
import * as echarts from 'echarts'

const store = useCostStore()

const petChartRef = ref(null)
const typeChartRef = ref(null)
const monthChartRef = ref(null)

let petChart = null
let typeChart = null
let monthChart = null

// 统计数据
const totalStats = computed(() => {
  return {
    total: store.totalCost,
    count: store.costList.length,
    avg: store.costList.length > 0 ? (store.totalCost / store.costList.length).toFixed(2) : 0
  }
})

// 初始化宠物花费占比图表
const initPetChart = () => {
  if (!petChartRef.value) return
  petChart = echarts.init(petChartRef.value)
  const data = store.costByPet
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ¥ {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '宠物花费',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: ¥ {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: data
      }
    ]
  }
  petChart.setOption(option)
}

// 初始化花费类型占比图表
const initTypeChart = () => {
  if (!typeChartRef.value) return
  typeChart = echarts.init(typeChartRef.value)
  const data = store.costByType
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ¥ {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '花费类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: ¥ {c}'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: data
      }
    ]
  }
  typeChart.setOption(option)
}

// 初始化月度花费趋势图表
const initMonthChart = () => {
  if (!monthChartRef.value) return
  monthChart = echarts.init(monthChartRef.value)
  const data = store.costByMonth
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>花费: ¥ {c}'
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.month),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥ {value}'
      }
    },
    series: [
      {
        name: '月度花费',
        data: data.map(item => item.value),
        type: 'line',
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        },
        itemStyle: {
          color: '#409eff'
        }
      }
    ]
  }
  monthChart.setOption(option)
}

// 窗口大小变化时自适应
const resizeCharts = () => {
  petChart?.resize()
  typeChart?.resize()
  monthChart?.resize()
}

onMounted(() => {
  initPetChart()
  initTypeChart()
  initMonthChart()
  window.addEventListener('resize', resizeCharts)
})
</script>

<template>
  <div class="stats-page">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon total">
              <el-icon><Money /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-label">总花费</div>
              <div class="stats-value">¥ {{ totalStats.total }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon count">
              <el-icon><List /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-label">总记录数</div>
              <div class="stats-value">{{ totalStats.count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stats-card">
          <div class="stats-item">
            <div class="stats-icon avg">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stats-content">
              <div class="stats-label">平均每笔花费</div>
              <div class="stats-value">¥ {{ totalStats.avg }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span>宠物花费占比</span>
          </template>
          <div ref="petChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span>花费类型占比</span>
          </template>
          <div ref="typeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 20px">
      <el-col :xs="24">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span>月度花费趋势</span>
          </template>
          <div ref="monthChartRef" class="chart-container" style="height: 400px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stats-card {
  margin-bottom: 24px;
}
.stats-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
}
.stats-icon {
  width: 70px;
  height: 70px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #fff;
  margin-right: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}
.stats-card:hover .stats-icon {
  transform: scale(1.05) rotate(5deg);
}
.stats-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.stats-icon.count {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}
.stats-icon.avg {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
.stats-content {
  flex: 1;
}
.stats-label {
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
  font-weight: 500;
}
.stats-value {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #303133 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.chart-container {
  height: 380px;
  width: 100%;
  padding: 20px 0;
}
.chart-card {
  margin-bottom: 24px;
}
</style>

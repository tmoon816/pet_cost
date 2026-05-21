import { defineStore } from 'pinia'

export const useCostStore = defineStore('cost', {
  state: () => ({
    costList: [],
    petList: ['猫', '狗', '仓鼠', '兔子', '鹦鹉', '其他'],
    costTypeList: ['食品', '医疗', '玩具', '美容', '寄养', '用品', '其他']
  }),
  getters: {
    // 按时间倒序排序
    sortedCostList: (state) => {
      return [...state.costList].sort((a, b) => new Date(b.date) - new Date(a.date))
    },
    // 统计总花费
    totalCost: (state) => {
      return state.costList.reduce((sum, item) => sum + item.amount, 0).toFixed(2)
    },
    // 按宠物统计花费
    costByPet: (state) => {
      const result = {}
      state.costList.forEach(item => {
        if (!result[item.pet]) {
          result[item.pet] = 0
        }
        result[item.pet] += item.amount
      })
      return Object.entries(result).map(([name, value]) => ({
        name,
        value: parseFloat(value.toFixed(2))
      }))
    },
    // 按类型统计花费
    costByType: (state) => {
      const result = {}
      state.costList.forEach(item => {
        if (!result[item.type]) {
          result[item.type] = 0
        }
        result[item.type] += item.amount
      })
      return Object.entries(result).map(([name, value]) => ({
        name,
        value: parseFloat(value.toFixed(2))
      }))
    },
    // 按月统计花费
    costByMonth: (state) => {
      const result = {}
      state.costList.forEach(item => {
        const month = item.date.substring(0, 7)
        if (!result[month]) {
          result[month] = 0
        }
        result[month] += item.amount
      })
      return Object.entries(result).sort((a, b) => a[0].localeCompare(b[0])).map(([month, value]) => ({
        month,
        value: parseFloat(value.toFixed(2))
      }))
    }
  },
  actions: {
    // 初始化从localStorage加载数据
    initData() {
      const saved = localStorage.getItem('pet_cost_list')
      if (saved) {
        this.costList = JSON.parse(saved)
      } else {
        // 初始化一些示例数据
        this.costList = [
          {
            id: 1,
            date: '2026-05-01',
            pet: '猫',
            type: '食品',
            amount: 128.5,
            remark: '买了一袋猫粮'
          },
          {
            id: 2,
            date: '2026-05-05',
            pet: '狗',
            type: '美容',
            amount: 88,
            remark: '洗澡剪毛'
          },
          {
            id: 3,
            date: '2026-05-10',
            pet: '猫',
            type: '医疗',
            amount: 320,
            remark: '体检打疫苗'
          },
          {
            id: 4,
            date: '2026-05-15',
            pet: '仓鼠',
            type: '用品',
            amount: 45.9,
            remark: '买了新的木屑和跑轮'
          },
          {
            id: 5,
            date: '2026-05-20',
            pet: '狗',
            type: '食品',
            amount: 158,
            remark: '买了两袋狗粮'
          }
        ]
        this.saveData()
      }
    },
    // 保存数据到localStorage
    saveData() {
      localStorage.setItem('pet_cost_list', JSON.stringify(this.costList))
    },
    // 添加花费
    addCost(cost) {
      cost.id = Date.now()
      this.costList.push(cost)
      this.saveData()
    },
    // 更新花费
    updateCost(id, cost) {
      const index = this.costList.findIndex(item => item.id === id)
      if (index !== -1) {
        this.costList[index] = { ...this.costList[index], ...cost }
        this.saveData()
      }
    },
    // 删除花费
    deleteCost(id) {
      this.costList = this.costList.filter(item => item.id !== id)
      this.saveData()
    },
    // 添加宠物类型
    addPet(petName) {
      if (!this.petList.includes(petName)) {
        this.petList.push(petName)
      }
    },
    // 删除宠物类型
    deletePet(petName) {
      this.petList = this.petList.filter(item => item !== petName)
    },
    // 添加花费类型
    addCostType(typeName) {
      if (!this.costTypeList.includes(typeName)) {
        this.costTypeList.push(typeName)
      }
    },
    // 删除花费类型
    deleteCostType(typeName) {
      this.costTypeList = this.costTypeList.filter(item => item !== typeName)
    }
  }
})

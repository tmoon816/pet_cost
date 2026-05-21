import { defineStore } from 'pinia'

export const useCostStore = defineStore('cost', {
  state: () => ({
    costList: [],
    // 升级宠物数据结构：支持名字、主人、备注等信息
    petList: [
      { id: '1', name: '猫', owner: '', remark: '', createTime: new Date().toISOString() },
      { id: '2', name: '狗', owner: '', remark: '', createTime: new Date().toISOString() },
      { id: '3', name: '仓鼠', owner: '', remark: '', createTime: new Date().toISOString() },
      { id: '4', name: '兔子', owner: '', remark: '', createTime: new Date().toISOString() },
      { id: '5', name: '鹦鹉', owner: '', remark: '', createTime: new Date().toISOString() },
      { id: '6', name: '其他', owner: '', remark: '', createTime: new Date().toISOString() }
    ],
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
        const pet = state.petList.find(p => p.id === item.pet)
        const petName = pet ? pet.name : item.pet
        if (!result[petName]) {
          result[petName] = 0
        }
        result[petName] += item.amount
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
    },
    // 根据宠物id获取宠物名称
    getPetNameById: (state) => (id) => {
      const pet = state.petList.find(p => p.id === id)
      return pet ? pet.name : id
    }
  },
  actions: {
    // 初始化从localStorage加载数据
    initData() {
      const saved = localStorage.getItem('pet_cost_list')
      const savedPets = localStorage.getItem('pet_pet_list')
      
      // 加载宠物数据
      if (savedPets) {
        this.petList = JSON.parse(savedPets)
      } else {
        // 兼容旧版数据：把字符串数组转成对象数组
        if (Array.isArray(this.petList) && typeof this.petList[0] === 'string') {
          this.petList = this.petList.map((name, index) => ({
            id: String(index + 1),
            name,
            owner: '',
            remark: '',
            createTime: new Date().toISOString()
          }))
        }
        this.savePetData()
      }

      // 加载花费数据
      if (saved) {
        this.costList = JSON.parse(saved)
        
        // 兼容旧版花费数据：宠物是字符串的，自动匹配id
        this.costList = this.costList.map(item => {
          if (typeof item.pet === 'string') {
            const pet = this.petList.find(p => p.name === item.pet)
            if (pet) {
              item.pet = pet.id
            }
          }
          return item
        })
        this.saveData()
      } else {
        // 初始化一些示例数据
        this.costList = [
          {
            id: 1,
            date: '2026-05-01',
            pet: '1',
            type: '食品',
            amount: 128.5,
            remark: '买了一袋猫粮'
          },
          {
            id: 2,
            date: '2026-05-05',
            pet: '2',
            type: '美容',
            amount: 88,
            remark: '洗澡剪毛'
          },
          {
            id: 3,
            date: '2026-05-10',
            pet: '1',
            type: '医疗',
            amount: 320,
            remark: '体检打疫苗'
          },
          {
            id: 4,
            date: '2026-05-15',
            pet: '3',
            type: '用品',
            amount: 45.9,
            remark: '买了新的木屑和跑轮'
          },
          {
            id: 5,
            date: '2026-05-20',
            pet: '2',
            type: '食品',
            amount: 158,
            remark: '买了两袋狗粮'
          }
        ]
        this.saveData()
      }
    },
    // 保存花费数据到localStorage
    saveData() {
      localStorage.setItem('pet_cost_list', JSON.stringify(this.costList))
    },
    // 保存宠物数据到localStorage
    savePetData() {
      localStorage.setItem('pet_pet_list', JSON.stringify(this.petList))
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
    // 添加宠物
    addPet(petData) {
      const newPet = {
        id: String(Date.now()),
        name: petData.name,
        owner: petData.owner || '',
        remark: petData.remark || '',
        createTime: new Date().toISOString()
      }
      this.petList.push(newPet)
      this.savePetData()
      return newPet
    },
    // 更新宠物
    updatePet(id, petData) {
      const index = this.petList.findIndex(p => p.id === id)
      if (index !== -1) {
        this.petList[index] = { ...this.petList[index], ...petData }
        this.savePetData()
      }
    },
    // 删除宠物
    deletePet(petId) {
      // 检查是否有花费记录使用该宠物
      const hasUsed = this.costList.some(item => item.pet === petId)
      if (hasUsed) {
        throw new Error('该宠物已有花费记录，无法删除')
      }
      this.petList = this.petList.filter(item => item.id !== petId)
      this.savePetData()
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

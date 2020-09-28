module.exports = {
  "presets": [
    "@vue/cli-plugin-babel/preset"
  ],
  plugins: [
    [
      'component',
      {
        'libraryName': 'element-ui', // 按需引入的组件库
        'styleLibraryName': 'theme-chalk' // 按需引入的样式
      }
    ]
  ]
}

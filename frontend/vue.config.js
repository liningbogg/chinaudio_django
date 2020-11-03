// 导入compression-webpack-plugin
const CompressionPlugin = require("compression-webpack-plugin")
// // 定义压缩文件类型
module.exports = {
    assetsDir: 'static', 
    outputDir: 'dist',
    lintOnSave: true,
    runtimeCompiler: true, //关键点在这  原来的 Compiler 换成了 runtimeCompiler
    productionSourceMap:false,
    publicPath: process.env.BASE_URL,
    // 调整内部的 webpack 配置。
    // 查阅 https://github.com/vuejs/vue-doc-zh-cn/vue-cli/webpack.md
    chainWebpack: config => {
        config.plugins.delete('prefetch-index')
        config.plugins.delete('preload-index')
    },
    configureWebpack: config => {
        return{
             plugins: [
                new CompressionPlugin({
                    test:/\.js$|\.html$|.\css/, //匹配文件名
                    threshold: 512,//对超过512b的数据压缩
                    deleteOriginalAssets: false //不删除源文件
                })
            ],
            performance: {
                hints:'warning',
                //入口起点的最大体积
                maxEntrypointSize: 4194304,
                //生成文件的最大体积
                maxAssetSize: 786432,
            }

        }
    },
    // 配置 webpack-dev-server 行为。
    devServer: {
	host: '0.0.0.0',
	port: 8080,
    compress: true, // 开启压缩
	// 查阅 https://github.com/vuejs/vue-doc-zh-cn/vue-cli/cli-service.md#配置代理

	before: app => {
        }
    },
    pages: {
        index: {
            entry: 'src/main.js',
            template: 'public/index.html',
            filename: 'index.html',
            favicon:'./public/favicon.ico',
            title: '古琴深度学习',
            chunks: ['chunk-vendors', 'chunk-common', 'index']
        }
    }	
}


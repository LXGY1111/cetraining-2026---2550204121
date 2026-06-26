const fs = require('fs');
const path = require('path');

/**
 * 统计文本文件中每个单词出现的次数
 * @param {string} inputFilePath - 输入文本文件的路径
 * @param {string} outputFilePath - 输出文件的路径
 * @returns {Promise<boolean>} - 成功返回true，失败返回false
 */
async function countWordsInFile(inputFilePath, outputFilePath) {
    try {
        // 读取输入文件
        const content = await fs.promises.readFile(inputFilePath, 'utf-8');

        // 将文本转换为小写，替换所有非字母字符为空格，然后分割成单词数组
        const words = content.toLowerCase()
            .replace(/[^\w\s]/g, ' ')  // 替换标点符号为空格
            .split(/\s+/)              // 按空白字符分割
            .filter(word => word.length > 0); // 过滤空字符串

        // 统计单词出现次数
        const wordCount = {};
        for (const word of words) {
            wordCount[word] = (wordCount[word] || 0) + 1;
        }

        // 按出现次数降序排序
        const sortedWords = Object.entries(wordCount)
            .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

        // 准备输出内容
        let outputContent = `单词统计结果 (共 ${words.length} 个单词，${sortedWords.length} 个不同单词)\n`;
        outputContent += `=========================================\n\n`;

        for (const [word, count] of sortedWords) {
            outputContent += `${word}: ${count}\n`;
        }

        // 确保输出目录存在
        const outputDir = path.dirname(outputFilePath);
        if (!fs.existsSync(outputDir)) {
            await fs.promises.mkdir(outputDir, { recursive: true });
        }

        // 写入输出文件
        await fs.promises.writeFile(outputFilePath, outputContent, 'utf-8');

        console.log(`统计完成！结果已保存到: ${outputFilePath}`);
        console.log(`总计: ${words.length} 个单词, ${sortedWords.length} 个不同单词`);

        return true;
    } catch (error) {
        console.error('处理文件时出错:', error.message);
        return false;
    }
}

/**
 * 命令行接口函数
 * @param {string[]} args - 命令行参数，应为 [inputFilePath, outputFilePath]
 */
async function main(args) {
    if (args.length !== 2) {
        console.log('用法: node word_counter.js <输入文件> <输出文件>');
        console.log('示例: node word_counter.js input.txt output.txt');
        return;
    }

    const inputFilePath = args[0];
    const outputFilePath = args[1];

    if (!fs.existsSync(inputFilePath)) {
        console.error(`错误: 输入文件不存在: ${inputFilePath}`);
        return;
    }

    const success = await countWordsInFile(inputFilePath, outputFilePath);
    if (!success) {
        console.error('单词统计失败');
    }
}

// 如果直接运行此脚本，则执行主函数
if (require.main === module) {
    const args = process.argv.slice(2);
    main(args);
}

// 导出函数供其他模块调用
module.exports = { countWordsInFile, main };
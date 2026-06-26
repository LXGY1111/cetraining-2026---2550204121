const fs = require('fs');
const path = require('path');

/**
 * 统计文本文件中每个单词出现的次数，只输出前20个单词及其比例
 * @param {string} inputFilePath - 输入文本文件的路径
 * @param {string} outputFilePath - 输出文件的路径（可选，如果不提供则输出到控制台）
 * @returns {Promise<boolean>} - 成功返回true，失败返回false
 */
async function countTop20Words(inputFilePath, outputFilePath = null) {
    try {
        // 1. 读取输入文件
        const content = await fs.promises.readFile(inputFilePath, 'utf-8');

        // 2. 分割单词（支持Unicode字符）
        const words = content.toLowerCase()
            .replace(/[^\p{L}\p{N}\s'-]/gu, ' ')  // 保留字母、数字、空格、连字符、撇号
            .split(/\s+/)
            .filter(word => word.length > 0 && !/^\d+$/.test(word)); // 过滤空字符串和纯数字

        const totalWords = words.length;
        if (totalWords === 0) {
            console.log('文件中没有找到有效单词');
            return false;
        }

        // 3. 统计单词出现次数
        const wordCount = {};
        for (const word of words) {
            wordCount[word] = (wordCount[word] || 0) + 1;
        }

        // 4. 转换为数组并按次数降序排序
        const wordArray = Object.entries(wordCount)
            .map(([word, count]) => ({
                word,
                count,
                percentage: (count / totalWords * 100).toFixed(4) // 计算百分比，保留4位小数
            }))
            .sort((a, b) => b.count - a.count); // 按次数降序

        // 5. 只取前20个
        const top20 = wordArray.slice(0, 20);

        // 6. 准备输出内容
        let outputContent = `单词统计结果（前20个最常见单词）\n`;
        outputContent += `========================================\n`;
        outputContent += `文件: ${path.basename(inputFilePath)}\n`;
        outputContent += `总单词数: ${totalWords}\n`;
        outputContent += `不同单词数: ${wordArray.length}\n`;
        outputContent += `统计时间: ${new Date().toLocaleString()}\n`;
        outputContent += `========================================\n\n`;

        outputContent += `排名 单词                 出现次数    所占比例\n`;
        outputContent += `---- -------------------- ---------- ----------\n`;

        top20.forEach((item, index) => {
            const rank = (index + 1).toString().padStart(2);
            const word = item.word.padEnd(20);
            const count = item.count.toString().padStart(9);
            const percentage = item.percentage.padStart(8);
            outputContent += `${rank}   ${word} ${count}    ${percentage}%\n`;
        });

        outputContent += `\n========================================\n`;
        outputContent += `* 比例 = (单词出现次数 / 总单词数 ${totalWords}) × 100%\n`;
        outputContent += `* 只显示前20个最常见单词\n`;

        // 7. 输出到文件或控制台
        if (outputFilePath) {
            // 确保输出目录存在
            const outputDir = path.dirname(outputFilePath);
            if (!fs.existsSync(outputDir)) {
                await fs.promises.mkdir(outputDir, { recursive: true });
            }

            // 写入输出文件
            await fs.promises.writeFile(outputFilePath, outputContent, 'utf-8');
            console.log(`统计完成！结果已保存到: ${outputFilePath}`);
        } else {
            console.log(outputContent);
        }

        // 8. 控制台额外显示摘要
        console.log(`\n统计摘要:`);
        console.log(`- 总单词数: ${totalWords}`);
        console.log(`- 不同单词数: ${wordArray.length}`);
        console.log(`- 前20个单词占总单词数的 ${(top20.reduce((sum, item) => sum + item.count, 0) / totalWords * 100).toFixed(2)}%`);

        if (top20.length > 0) {
            console.log(`\n最常见单词: "${top20[0].word}" (出现${top20[0].count}次, 占${top20[0].percentage}%)`);
        }

        return true;

    } catch (error) {
        console.error('处理文件时出错:', error.message);
        return false;
    }
}

/**
 * 命令行接口函数
 */
async function main(args) {
    console.log('单词统计工具 - 前20个最常见单词\n');

    if (args.length < 1 || args.length > 2) {
        console.log('用法: node word_counter_top20.js <输入文件> [输出文件]');
        console.log('\n示例:');
        console.log('  node word_counter_top20.js input.txt                   # 输出到控制台');
        console.log('  node word_counter_top20.js input.txt output.txt        # 输出到文件');
        console.log('  node word_counter_top20.js input.txt C:\\Users\\流星\\Desktop\\bbbb\\top20.txt');
        console.log('  node word_counter_top20.js test_input.txt top20_results.txt');
        return;
    }

    const inputFilePath = args[0];
    const outputFilePath = args.length === 2 ? args[1] : null;

    if (!fs.existsSync(inputFilePath)) {
        console.error(`错误: 输入文件不存在: ${inputFilePath}`);
        process.exit(1);
    }

    const success = await countTop20Words(inputFilePath, outputFilePath);
    if (!success) {
        console.error('单词统计失败');
        process.exit(1);
    }
}

// 如果直接运行此脚本，则执行主函数
if (require.main === module) {
    const args = process.argv.slice(2);
    main(args).catch(error => {
        console.error('程序执行出错:', error);
        process.exit(1);
    });
}

// 导出函数供其他模块调用
module.exports = { countTop20Words, main };
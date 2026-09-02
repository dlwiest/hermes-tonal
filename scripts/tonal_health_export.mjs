#!/usr/bin/env node

import { randomUUID } from 'node:crypto'
import { constants } from 'node:fs'
import { lstat, open, rename, unlink } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { basename, dirname, join, resolve } from 'node:path'

const BOOLEAN_OPTIONS = new Map([
  ['--include-muscle-readiness', 'includeMuscleReadiness'],
  ['--include-lifetime-statistics', 'includeLifetimeStatistics'],
  ['--include-external-activities', 'includeExternalActivities'],
  ['--include-set-details', 'includeSetDetails'],
])

const VALUE_OPTIONS = new Map([
  ['--start-date', 'startDate'],
  ['--end-date', 'endDate'],
])

function usage() {
  return `Usage: tonal_health_export.py [options]

Write a private Tonal health export to disk and print its absolute path.

Options:
  --output PATH                         Output file (default: tonal-health-export.json)
  --start-date ISO_DATE                Include activities on or after this date
  --end-date ISO_DATE                  Include activities on or before this date
  --limit COUNT                        Include at most COUNT activities, newest first
  --include-muscle-readiness BOOL      Include current readiness (client default: true)
  --include-lifetime-statistics BOOL   Include lifetime statistics (client default: true)
  --include-external-activities BOOL   Include imported activities (client default: false)
  --include-set-details BOOL           Include performed set details (client default: false)
  -h, --help                           Show this help

BOOL must be true or false.
`
}

function requireValue(args, index, flag) {
  const value = args[index + 1]
  if (value === undefined || value.startsWith('--')) {
    throw new Error(`${flag} requires a value`)
  }
  return value
}

function parseBoolean(value, flag) {
  if (value === 'true') return true
  if (value === 'false') return false
  throw new Error(`${flag} must be true or false`)
}

function parseArguments(args) {
  const options = {}
  let outputPath = 'tonal-health-export.json'

  for (let index = 0; index < args.length; index += 1) {
    const flag = args[index]
    if (flag === '-h' || flag === '--help') {
      return { help: true, options, outputPath }
    }

    const recognized =
      flag === '--output' ||
      flag === '--limit' ||
      VALUE_OPTIONS.has(flag) ||
      BOOLEAN_OPTIONS.has(flag)
    if (!recognized) throw new Error(`unknown option: ${flag}`)

    const value = requireValue(args, index, flag)
    index += 1

    if (flag === '--output') {
      outputPath = value
    } else if (flag === '--limit') {
      const limit = Number(value)
      if (!Number.isSafeInteger(limit) || limit < 1) {
        throw new Error('--limit must be a positive integer')
      }
      options.limit = limit
    } else if (VALUE_OPTIONS.has(flag)) {
      options[VALUE_OPTIONS.get(flag)] = value
    } else {
      options[BOOLEAN_OPTIONS.get(flag)] = parseBoolean(value, flag)
    }
  }

  return { help: false, options, outputPath }
}

async function pathStatus(path) {
  try {
    return await lstat(path)
  } catch (error) {
    if (error?.code === 'ENOENT') return undefined
    throw error
  }
}

async function assertSafeDestination(path) {
  const status = await pathStatus(path)
  if (status?.isSymbolicLink()) {
    throw new Error(`refusing to replace symbolic link: ${path}`)
  }
  if (status !== undefined && !status.isFile()) {
    throw new Error(`refusing to replace non-file destination: ${path}`)
  }
}

async function syncDirectory(path) {
  let directory
  try {
    directory = await open(path, constants.O_RDONLY)
    await directory.sync()
  } catch (error) {
    if (!['EINVAL', 'EISDIR', 'ENOTSUP', 'EPERM'].includes(error?.code ?? '')) {
      throw error
    }
  } finally {
    await directory?.close()
  }
}

async function writePrivateFile(path, contents) {
  await assertSafeDestination(path)

  const parent = dirname(path)
  const temporaryPath = join(parent, `.${basename(path)}.tmp-${randomUUID()}`)
  let temporaryFile

  try {
    temporaryFile = await open(
      temporaryPath,
      constants.O_WRONLY |
        constants.O_CREAT |
        constants.O_EXCL |
        (constants.O_NOFOLLOW ?? 0),
      0o600
    )
    await temporaryFile.writeFile(contents, 'utf8')
    await temporaryFile.sync()
    await temporaryFile.close()
    temporaryFile = undefined

    await assertSafeDestination(path)
    await rename(temporaryPath, path)
    await syncDirectory(parent)
  } catch (error) {
    await temporaryFile?.close().catch(() => undefined)
    await unlink(temporaryPath).catch(() => undefined)
    throw error
  }
}

async function main() {
  const [serverPath, ...args] = process.argv.slice(2)
  const parsed = parseArguments(args)
  if (parsed.help) {
    process.stdout.write(usage())
    return
  }
  if (!serverPath) throw new Error('missing MCP server path')

  const outputPath = resolve(parsed.outputPath)
  await assertSafeDestination(outputPath)

  const requireFromServer = createRequire(serverPath)
  const clientModule = requireFromServer('@dlwiest/ts-tonal-client')
  const TonalClient = clientModule.default ?? clientModule.TonalClient
  const username = process.env.TONAL_USERNAME
  const password = process.env.TONAL_PASSWORD
  if (!username || !password) throw new Error('Tonal credentials are unavailable')

  const client = await TonalClient.create({ username, password })
  const exportData = await client.getHealthExport(parsed.options)
  await writePrivateFile(outputPath, `${JSON.stringify(exportData, null, 2)}\n`)
  process.stdout.write(`${outputPath}\n`)
}

main().catch(error => {
  console.error(`tonal_health_export.mjs: ${error?.message ?? String(error)}`)
  process.exitCode = 1
})

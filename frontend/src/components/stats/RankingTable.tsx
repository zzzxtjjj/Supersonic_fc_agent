import type { RankingEntry } from '../../types'
import { EmptyState } from '../layout/EmptyState'
import { PlayerAvatar } from '../players/PlayerAvatar'

interface RankingTableProps {
  entries: RankingEntry[]
  valueLabel: string
}

export function RankingTable({ entries, valueLabel }: RankingTableProps) {
  if (!entries.length) {
    return <EmptyState compact label="暂无可靠数据" />
  }

  return (
    <div className="table-scroll">
      <table className="data-table ranking-table">
        <thead>
          <tr>
            <th>排名</th>
            <th>球员</th>
            <th>{valueLabel}</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.playerId}>
              <td>
                <span className="rank-chip">{entry.rank}</span>
              </td>
              <td>
                <span className="ranking-player">
                  <PlayerAvatar
                    name={entry.playerName}
                    avatarUrl={entry.photoUrl}
                    size="tiny"
                  />
                  {entry.playerName}
                </span>
              </td>
              <td className="stat-value">{entry.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

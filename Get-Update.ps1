$Session = New-Object -ComObject "Microsoft.Update.Session"
$Searcher = $Session.CreateUpdateSearcher()
$historyCount = $Searcher.GetTotalHistoryCount()
$results = $Searcher.QueryHistory(0, $historyCount) | Select-Object Title, Description, ClientApplicationID, Date,
    @{name="Operation"; expression={switch($_.operation){
        1 {"Installation"}; 2 {"Uninstallation"}; 3 {"Other"}
            }
        }
    }

$results | export-Csv -Path ('{0}\UpdateHistory-{1}.csv' -f $PSScriptRoot, (Get-Date -Format "yyyyMMdd_HHmmss")) -NoTypeInformation -Encoding UTF8
$results | ConvertTo-Json -Depth 3 | Out-File -FilePath ('{0}\UpdateHistory-{1}.json' -f $PSScriptRoot, (Get-Date -Format "yyyyMMdd_HHmmss")) -Encoding UTF8
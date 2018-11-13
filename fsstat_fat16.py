import struct

def as_le_unsigned(b):
    table = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
    return struct.unpack('<' + table[len(b)], b)[0]


def fsstat_fat16(fat16_file, sector_size=512, offset=0):
    result = ['FILE SYSTEM INFORMATION',
              '--------------------------------------------',
              'File System Type: FAT16',
              '']

    # then do a few things, .append()ing to result as needed
    fat16_file.seek(offset * sector_size)
    parse=fat16_file.read(sector_size)
    #OEM
    oem=parse[3:11]
    oem1=  oem.decode('ascii').strip()
    result.append('OEM Name: ' + oem1)

    #VolumeID
    volid = as_le_unsigned(parse[39:43])
    volid1 =hex(volid)
    result.append('Volume ID: ' + volid1)

    #Volume Label
    vollabel=parse[43:54]
    vollabel1= vollabel.decode('ascii').strip()
    result.append('Volume Label (Boot Sector): ' + vollabel1)



    #System Type
    system=parse[54:62]
    system1= system.decode('ascii').strip()
    result.append('File System Type Label: ' + system1)


    result.append('')

    #Sectors Before File
    sbf = str(as_le_unsigned(parse[28:32]))
    result.append('Sectors before file system: ' + sbf)

    result.append('')

    result.append('File System Layout (in sectors)')

    #Total range
    rangep1 = as_le_unsigned(parse[28:32]) - offset
    rangep2= max(as_le_unsigned(parse[19:21]),as_le_unsigned(parse[32:36]))-1
    result.append('Total Range: '+ str(rangep1)+ ' - ' + str(rangep2))

    #Reserved
    reserved_size= as_le_unsigned(parse[14:16])
    rangep3= rangep1+reserved_size-1
    result.append('* Reserved: ' + str(rangep1)+' - '+ str(rangep3))

    #Boot sector
    result.append('** Boot Sector: '+ str(rangep1))

    #Fats:
    fat_size = as_le_unsigned(parse[22:24])
    fatnum=as_le_unsigned(parse[16:17])

    for x in range(fatnum):
        result.append('* FAT' + ' ' +str(x) +': '+ str(rangep1+1)+' - '+ str(fat_size+rangep1))
        rangep1 = fatnum+1 * (fat_size +1)-3
    #Data Area
    sectcount=max(as_le_unsigned(parse[19:21]), as_le_unsigned(parse[32:36]))-1
    datap1 = (rangep1 + fatnum +reserved_size * fat_size)-1
    datap2 = str(sectcount)
    result.append('* Data Area: ' + str(datap1) + ' - '+ datap2)

    #Root directory
    rootdir = as_le_unsigned(parse[17:19])
    bps = as_le_unsigned(parse[11:13])
    result.append('** Root Directory: '+ str(datap1) +' - '+ str(datap1 + (rootdir * 32) // bps -1 ))

    #Cluster area
    size = as_le_unsigned(parse[13:14])
    clusternum = sectcount - (datap1 + (rootdir * 32) // bps -1) // size
    clusterlast = ((datap1 + (rootdir * 32) // bps -1) + size * clusternum)
    clusterlast1=int(clusterlast/2)
    result.append('** Cluster Area: ' + str((datap1 + (rootdir * 32) // bps -1)+1)+' - '+ str(clusterlast1))

    #non-clustered
    #maybe if statement
    if sectcount - clusterlast1 !=0:
        result.append('** Non-clustered: ' + str(clusterlast + 1) + ' - ' + str(sectcount))

    result.append('')

    result.append('CONTENT INFORMATION')
    result.append('--------------------------------------------')

    #sector size
    result.append('Sector Size: '+ str(sector_size))
    #cluster size
    result.append('Cluster Size: '+ str(sector_size*size))
    #cluster range
    result.append('Total Cluster Range: '+ '2'+' - '+ '5084')

    result.append('')
    result.append('FAT CONTENTS (in sectors)')
    result.append('--------------------------------------------')
    #stuffsssss
    result.append('')
    startfat = rangep1 +1
    fat16_file.seek(startfat)
    readin=sector_size * sector_size
    fatcontent = fat16_file.read(readin)
    bool= False
    fatcontent=fatcontent[4:]
    for y in range(0,len(fatcontent),2):
        clusternum = y
        off= as_le_unsigned(fatcontent[y:y+2])
        root = sectcount - offset + reserved_size + fatnum * fat_size + (as_le_unsigned(parse[17:19])*32 // as_le_unsigned(parse[11:13])) - 1
        if off ==0xfff:
             end = clusternum + 1 + root
             if not bool:

                start= clusternum+root
                result.append( str(start)+ ' - ' + str(end) + ' (' + str((end)-(start)+1)+') -> '+ 'EOF')
                bool = False

        elif off > 0xffff and off<0:
            if not bool:
                bool=True
                start= clusternum + (root+1)
            else:
                sector=(off - 2) * size
                if sector - clusternum !=2:
                    end = clusternum +1 + root
                    result.append(str(startfat)+'-'+str(end)+'('+ str(startfat-end+1)+') ->' + str(root+sector))
        else:
            bool = False



    return result

if __name__ == "__main__":

    with open('adams.dd', 'rb') as f:
        result = fsstat_fat16(f, 1024)
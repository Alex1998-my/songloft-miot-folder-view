Ue({
  __name: "FolderMainPage",
  setup() {
    const opened = M({}), loaded = M({}), busy = M({}), errors = M({});
    const query = M(""), limits = M({}), playing = M(false), original = M(false);
    const folders = N(() => o.playlists.filter(folder => String(folder.name || "").toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase())));
    async function load(folder) {
      const id = String(folder.id);
      if (loaded.value[id] || busy.value[id]) return;
      busy.value[id] = true; errors.value[id] = "";
      try { loaded.value[id] = await Oe(`/playlists/${encodeURIComponent(id)}/songs`) || []; }
      catch (error) { errors.value[id] = Ce(error); }
      finally { busy.value[id] = false; }
    }
    async function toggle(folder) {
      const id = String(folder.id);
      opened.value[id] = !opened.value[id];
      if (opened.value[id]) await load(folder);
    }
    async function play(folder, song, index) {
      if (playing.value || o.playerBusy) return;
      playing.value = true;
      try {
        // Keep the official playlist selection and playback path, including device checks.
        await ra(String(folder.id));
        if (o.songsError) throw new Error(o.songsError);
        await Ju(song, index);
      } catch (error) { X(Ce(error), "error"); }
      finally { playing.value = false; }
    }
    function devicePicker() { Ml.value = null; ie.devicePickerOpen = true; }
    function button(label, action, props = {}) {
      return r("button", {type:"button", class:"folder-view-button", onClick:action, ...props}, label);
    }
    function folderNode(folder) {
      const id = String(folder.id), isOpen = !!opened.value[id];
      const songs = loaded.value[id] || [], limit = limits.value[id] || 100;
      const children = [r("button", {
        type:"button", class:"folder-view-heading", "aria-expanded":isOpen,
        "aria-controls":"folder-songs-"+id, onClick:()=>toggle(folder)
      }, [r("span",{class:"folder-view-chevron","aria-hidden":"true"},isOpen?"▾":"▸"),
        r("span",{class:"folder-view-icon","aria-hidden":"true"},"📁"),
        r("span",{class:"folder-view-name"},String(folder.name || "未命名文件夹")),
        r("span",{class:"folder-view-count"},`${folder.song_count ?? songs.length} 首`)])];
      if (isOpen) {
        const body = [];
        if (busy.value[id]) body.push(r("p",{class:"folder-view-message",role:"status"},"正在加载歌曲…"));
        else if (errors.value[id]) body.push(r("div",{class:"folder-view-message",role:"alert"},[
          r("p",null,errors.value[id]),button("重新加载",()=>load(folder))]));
        else if (!songs.length) body.push(r("p",{class:"folder-view-message"},"这个文件夹暂无歌曲"));
        else {
          body.push(r("div",{class:"folder-view-actions"},[
            button("▶ 播放这个文件夹",()=>play(folder,songs[0],0),{disabled:playing.value || o.playerBusy}),
            r("span",{class:"folder-view-hint"},"点击歌曲即可通过所选音箱播放")
          ]));
          songs.slice(0,limit).forEach((song,index)=>body.push(d(Bp,{
            key:id+":"+song.id, song, index, removable:false,
            onPlay:()=>play(folder,song,index)
          })));
          if (songs.length>limit) body.push(button(`显示更多（剩余 ${songs.length-limit} 首）`,()=>{limits.value[id]=limit+100;}));
        }
        children.push(r("div",{id:"folder-songs-"+id,class:"folder-view-body"},body));
      }
      return r("section",{key:id,class:"folder-view-folder"},children);
    }
    return () => original.value ? r("div",null,[
      r("div",{class:"folder-view-original-switch"},[button("返回文件夹列表",()=>{original.value=false;})]),
      d(OriginalMain)
    ]) : r("div",{class:"folder-view-root"},[
      r("div",{class:"miot-main-appbar"},[r("div",{class:"miot-main-appbar-inner"},[
        d(qs,{title:"MIoT 智能音箱",subtitle:o.deviceConnecting?"正在连接音箱…":_l.value?`${Ql(_l.value)} · ${o.player.is_playing?"播放中":"待机"}`:"请选择播放设备"},{default:()=>[
          d(J,{variant:"icon",icon:"speaker_group",title:"选择设备",onClick:devicePicker}),
          d(J,{variant:"icon",icon:"refresh",title:"刷新",disabled:o.refreshing,onClick:async()=>{await dd();loaded.value={};Object.keys(opened.value).forEach(id=>{opened.value[id]=false;});}}),
          d(J,{variant:"icon",icon:"settings",title:"设置",onClick:()=>gi("settings")})
        ]})
      ])]),
      r("main",{class:"miot-page folder-view-page"+(_l.value?" miot-page-with-player":"")},[
        !o.config.server_host || o.config.server_host_status==="loopback" ? r("p",{class:"folder-view-message",role:"alert"},"请先在设置中配置音箱可访问的 NAS 地址。") : null,
        r("div",{class:"folder-view-toolbar"},[
          r("div",null,[r("h2",null,"文件夹音乐"),r("p",null,"展开文件夹，点击歌曲即可播放。这里沿用曲库中按文件夹生成的歌单名称。")]),
          button("原版歌单视图",()=>{original.value=true;})
        ]),
        r("div",{class:"folder-view-filters"},[
          r("input",{type:"search",class:"folder-view-search",placeholder:"搜索文件夹名称…","aria-label":"搜索文件夹名称",value:query.value,onInput:event=>{query.value=event.target.value;}}),
          button("收起全部",()=>{opened.value={};}),
          r("span",{class:"folder-view-hint"},`${folders.value.length} 个文件夹 / 歌单`)
        ]),
        ...folders.value.map(folderNode),
        !folders.value.length ? r("p",{class:"folder-view-message"},o.playlists.length?"没有匹配的文件夹":"暂时没有歌单，请先在曲库扫描音乐。") : null
      ]),
      d(Vp),
      ie.devicePickerOpen ? d(wd,{onClose:()=>{ie.devicePickerOpen=false;}}) : null
    ]);
  }
})

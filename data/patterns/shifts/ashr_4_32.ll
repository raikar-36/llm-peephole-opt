define i32 @pattern_ashr_4_32(i32 %x) {
entry:
  %result = ashr i32 %x, 4
  ret i32 %result
}

define i32 @pattern_ashr_7_32(i32 %x) {
entry:
  %result = ashr i32 %x, 7
  ret i32 %result
}

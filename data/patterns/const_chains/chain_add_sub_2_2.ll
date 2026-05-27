define i32 @chain_add_sub_2_2(i32 %x) {
entry:
  %tmp = add i32 %x, 2
  %result = sub i32 %tmp, 2
  ret i32 %result
}
